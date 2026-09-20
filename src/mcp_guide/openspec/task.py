"""OpenSpec CLI detection task."""

import json
import re
import time
from typing import TYPE_CHECKING, Any, Optional, cast

from packaging.version import InvalidVersion, Version

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_register
from mcp_guide.feature_flags.constants import FLAG_OPENSPEC, FLAG_OPENSPEC_STATE
from mcp_guide.feature_flags.types import FeatureValue, RawFeatureValue
from mcp_guide.feature_flags.validators import is_value_true
from mcp_guide.openspec.rendering import render_openspec_template
from mcp_guide.openspec.state import OpenSpecState, parse_openspec_state, serialise_openspec_state
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.runtime import get_runtime
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.protocol import DEFAULT_ONCE_INTERVAL, InitialisableMixin

if TYPE_CHECKING:
    from mcp_guide.task_manager.activation import TaskActivation
    from mcp_guide.task_manager.manager import EventResult

logger = get_logger(__name__)

# Cache constants
CHANGES_CACHE_TTL = 3600  # 1 hour
OPENSPEC_CHECK_INTERVAL = 24 * 60 * 60


@task_register
class OpenSpecTask(InitialisableMixin):
    """Task for detecting OpenSpec CLI availability."""

    configuration_flags = frozenset({FLAG_OPENSPEC, FLAG_OPENSPEC_STATE})

    def __init__(self) -> None:
        """Create an inactive OpenSpec task."""
        self.activation: TaskActivation | None = None
        self._session: Any = None
        self._detection_requested = False
        self._flag_checked = False
        self._available: Optional[bool] = None
        self._project_requested = False
        self._version: Optional[str] = None
        self._version_this_session: Optional[str] = None  # Session-level cache
        self._changes_cache: Optional[list[dict[str, Any]]] = None
        self._changes_timestamp: Optional[float] = None
        self._changes_directory_mtime: Optional[float] = None
        self._observed_changes_directory_mtime: Optional[float] = None
        self._changes_refresh_generation = 0
        self._pending_changes_refresh_id: Optional[str] = None
        self._changes_directory_refresh_id: Optional[str] = None

        # Instruction tracking IDs
        self._detection_instruction_id: Optional[str] = None
        self._project_instruction_id: Optional[str] = None

    async def start(self, activation: "TaskActivation") -> bool:
        """Start OpenSpec detection if enabled for the current project."""
        self.activation = activation
        self._session = activation.session
        if not await self._is_enabled():
            logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
            self._flag_checked = True
            return False

        activation.subscribe(
            EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY,
            once_interval=DEFAULT_ONCE_INTERVAL,
        )
        return True

    @property
    def _activation(self) -> "TaskActivation":
        """Return the task's activation after it has started."""
        if self.activation is None:
            raise RuntimeError("OpenSpec task is not active")
        return self.activation

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "OpenSpecTask"

    async def on_tool(self) -> None:
        pass

    async def _initialise(self) -> "EventResult":
        """Check flag and perform deferred initialization."""
        from mcp_guide.task_manager.manager import EventResult

        if self._session is None:
            return EventResult(result=False, message="OpenSpec task is not attached to a Session")
        openspec_enabled = await self._is_enabled()

        if not openspec_enabled:
            await self._activation.unsubscribe()
            logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
            self._flag_checked = True
            return EventResult(result=True)

        state = await self._get_global_state()
        if self._is_recent(state):
            self._available = state.validated
            self._version = state.version
            self._activation.set_cached_data("openspec_available", self._available)
            self._activation.set_cached_data("openspec_version", self._version)
            if state.validated and not self._project_requested:
                self._project_requested = True
                await self.request_project_check()
        elif not self._detection_requested:
            await self.request_detection()
            self._detection_requested = True
        self._flag_checked = True
        return EventResult(result=True)

    async def _is_enabled(self) -> bool:
        """Return whether the active Project exclusively enables OpenSpec."""
        if self._session is None:
            return False
        # Configuration publication invokes task restarts while it holds the
        # publication lock.  Read the Session's already-bound Project rather
        # than triggering a project refresh through project_flags(), which
        # could try to reacquire that lock for a malformed external update.
        project = self._session.project
        if project is None:
            return False
        value = project.project_flags.get(FLAG_OPENSPEC)
        return is_value_true(value)

    async def _get_global_state(self) -> OpenSpecState:
        """Load the machine-wide OpenSpec state through the feature-flag API."""
        value = await get_runtime().feature_flags().get(FLAG_OPENSPEC_STATE)
        return parse_openspec_state(value)

    @staticmethod
    def _is_recent(state: OpenSpecState) -> bool:
        """Return whether a completed global check remains within its guard period."""
        if state.checked is None:
            return False
        age = time.time() - state.checked
        return 0 <= age < OPENSPEC_CHECK_INTERVAL

    async def _persist_global_state(self, *, validated: bool, version: str | None = None) -> None:
        """Replace the complete machine-wide OpenSpec state after an attempt."""
        state = serialise_openspec_state(OpenSpecState(validated=validated, version=version, checked=time.time()))
        if state is None:
            raise RuntimeError("Completed OpenSpec state must serialise")
        await get_runtime().feature_flags().set(FLAG_OPENSPEC_STATE, FeatureValue(cast(RawFeatureValue, state)))

    def is_available(self) -> Optional[bool]:  # noqa: Vulture
        """Check if OpenSpec CLI is available.

        Returns:
            True if available, False if not available, None if not yet checked.
        """
        return self._available

    def get_version(self) -> Optional[str]:  # noqa: Vulture
        """Get OpenSpec CLI version.

        Returns:
            Version string (e.g., "1.2.3") or None if not available.
        """
        return self._version

    def meets_minimum_version(self, minimum: str) -> bool:  # noqa: Vulture
        """Check if current OpenSpec version meets minimum requirement.

        Args:
            minimum: Minimum version string (e.g., "1.2.0")

        Returns:
            True if current version >= minimum, False otherwise or if version unknown
        """
        if not self._version:
            return False

        try:
            # Strip 'v' prefix if present
            current = self._version.lstrip("v")
            min_ver = minimum.lstrip("v")
            return Version(current) >= Version(min_ver)
        except InvalidVersion:
            logger.warning(f"Invalid version comparison: current={self._version}, minimum={minimum}")
            return False

    def get_changes(self) -> Optional[dict[str, list[dict[str, Any]]]]:
        """Get cached OpenSpec changes list grouped by status.

        Returns:
            Dict with in_progress, draft, complete lists or None if not cached.
        """
        if not self.is_cache_valid():
            return None

        from datetime import datetime, timezone

        def humanize_date(iso_date: str) -> str:
            """Convert ISO date to human-readable format."""
            try:
                dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                delta = now - dt
                days = delta.days
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60

                if days > 0:
                    return f"{days}d{hours}h ago"
                elif hours > 0:
                    return f"{hours}h{minutes}m ago"
                else:
                    return f"{minutes}m ago"
            except Exception:
                return iso_date[:10]

        # Group changes by status
        in_progress: list[dict[str, Any]] = []
        draft: list[dict[str, Any]] = []
        complete: list[dict[str, Any]] = []

        if self._changes_cache is None:
            return {"in_progress": in_progress, "draft": draft, "complete": complete}

        for change in self._changes_cache:
            formatted = change.copy()
            completed = change.get("completedTasks", 0)
            total = change.get("totalTasks", 0)
            formatted["progress"] = f"{completed}/{total}" if total > 0 else "N/A"
            formatted["humanized_date"] = humanize_date(change.get("lastModified", ""))

            status = change.get("status", "")
            if status == "in-progress":
                in_progress.append(formatted)
            elif status == "no-tasks":
                draft.append(formatted)
            elif status == "complete":
                complete.append(formatted)

        return {"in_progress": in_progress, "draft": draft, "complete": complete}

    def get_show(self) -> Optional[dict[str, Any]]:
        """Get cached OpenSpec show data.

        Returns:
            Show data dict or None if not cached.
        """
        data = self._activation.get_cached_data("openspec_show")
        return data if isinstance(data, dict) else None

    def get_status(self) -> Optional[dict[str, Any]]:
        """Get cached OpenSpec status data.

        Returns:
            Status data dict or None if not cached.
        """
        data = self._activation.get_cached_data("openspec_status")
        return data if isinstance(data, dict) else None

    def is_cache_valid(self, ttl: int = CHANGES_CACHE_TTL) -> bool:
        """Check if changes cache is valid.

        Args:
            ttl: Time-to-live in seconds (default: CHANGES_CACHE_TTL)

        Returns:
            True if cache exists and is not expired, False otherwise.
        """
        if (
            self._changes_cache is None
            or self._changes_timestamp is None
            or self._changes_directory_mtime is None
            or self._observed_changes_directory_mtime is None
            or self._changes_directory_mtime != self._observed_changes_directory_mtime
        ):
            return False

        import time

        age = time.time() - self._changes_timestamp
        return age < ttl

    def prepare_changes_refresh(self, *, force: bool = False) -> str:
        """Return the opaque identifier for a requested changes refresh.

        A non-forced request reuses an in-flight refresh so concurrent renders
        cannot solicit indistinguishable replies. A forced request supersedes
        the prior refresh; replies carrying the old identifier are ignored.
        """
        if self._pending_changes_refresh_id is not None and not force:
            return self._pending_changes_refresh_id

        self._changes_refresh_generation += 1
        self._pending_changes_refresh_id = f"openspec-changes-{self._changes_refresh_generation}"
        self._changes_directory_refresh_id = None
        return self._pending_changes_refresh_id

    @property
    def changes_refresh_id(self) -> Optional[str]:
        """Return the identifier for the active changes refresh, if any."""
        return self._pending_changes_refresh_id

    def _is_current_changes_refresh(self, request_id: object) -> bool:
        """Return whether a filesystem reply belongs to the active refresh."""
        return isinstance(request_id, str) and request_id == self._pending_changes_refresh_id

    async def request_detection(self) -> None:
        """Request combined OpenSpec CLI detection from the client."""
        rendered = await render_openspec_template(self._session, "openspec-check")
        if rendered:
            self._detection_instruction_id = await self._activation.queue_instruction_with_ack(rendered.content)

    async def request_project_check(self) -> None:
        """Request OpenSpec project structure check from client."""
        rendered = await render_openspec_template(self._session, "openspec-project-check")
        if rendered:
            self._project_instruction_id = await self._activation.queue_instruction_with_ack(rendered.content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        """Handle task manager events."""
        from mcp_guide.task_manager.manager import EventResult

        if result := await self._handle_timer_once(event_type):
            return result

        # Handle directory listing events
        if event_type & EventType.FS_DIRECTORY:
            path = data.get("path", "")
            if path == "openspec":
                # Acknowledge project check instruction
                if self._project_instruction_id:
                    await self._activation.acknowledge_instruction(self._project_instruction_id)
                    self._project_instruction_id = None

                return EventResult(result=True)
            if path == "openspec/changes":
                request_id = data.get("request_id")
                if request_id is None:
                    # Preserve passive directory-mtime invalidation for clients
                    # that report a listing outside the explicit refresh flow.
                    # Such a listing can invalidate cached data, but cannot
                    # authorise a changes-list response for a pending refresh.
                    mtime = data.get("mtime")
                    self._observed_changes_directory_mtime = (
                        float(mtime) if isinstance(mtime, (int, float)) and not isinstance(mtime, bool) else None
                    )
                    return EventResult(result=True)
                if not self._is_current_changes_refresh(request_id):
                    logger.debug("Ignoring OpenSpec changes directory response for a superseded refresh")
                    return EventResult(result=True)
                mtime = data.get("mtime")
                self._observed_changes_directory_mtime = (
                    float(mtime) if isinstance(mtime, (int, float)) and not isinstance(mtime, bool) else None
                )
                self._changes_directory_refresh_id = request_id
                return EventResult(result=True)
            return None

        # Handle file content events
        if event_type & EventType.FS_FILE_CONTENT:
            from pathlib import Path

            path = data.get("path", "")
            path_name = Path(path).name

            if path_name == ".openspec-changes.json":
                request_id = data.get("request_id")
                if not self._is_current_changes_refresh(request_id) or request_id != self._changes_directory_refresh_id:
                    logger.debug("Ignoring OpenSpec changes response for a superseded or incomplete refresh")
                    return EventResult(result=True)

            if path_name == ".openspec-info.json":
                content = data.get("content", "")
                try:
                    report = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in OpenSpec detection response")
                    report = {}
                version = report.get("version") if isinstance(report, dict) else None
                await self._parse_detection(version if isinstance(version, str) else None)
                return EventResult(result=True)

            # Handle OpenSpec command responses
            content = data.get("content", "")

            # Parse JSON responses
            try:
                json_data = json.loads(content)
            except json.JSONDecodeError:
                logger.debug(f"Non-JSON content in {path_name}, skipping")
                return None

            # Check for error responses first
            if "error" in json_data:
                formatted = await self._format_error_response(json_data)
                if formatted:
                    return EventResult(
                        result=False,
                        message=formatted.content,
                        rendered_content=formatted,
                    )
                return EventResult(result=False, message="OpenSpec command error")

            # Format specific OpenSpec responses
            if path_name == ".openspec-status.json":
                # Cache the status data
                self._activation.set_cached_data("openspec_status", json_data)

                # Render and return the status format
                rendered = await render_openspec_template(
                    self._session, "_status-format", extra_context=TemplateContext(json_data)
                )
                if rendered:
                    return EventResult(
                        result=True,
                        message=f"File content cached for {path_name}",
                        rendered_content=rendered,
                    )
                return None

            elif path_name == ".openspec-changes.json":
                # Cache the changes data
                import time

                changes = json_data.get("changes", [])
                self._changes_cache = changes
                self._changes_timestamp = time.time()
                self._changes_directory_mtime = self._observed_changes_directory_mtime
                self._pending_changes_refresh_id = None
                self._changes_directory_refresh_id = None
                self._activation.set_cached_data("openspec_changes", changes)
                logger.debug(f"Cached {len(changes)} OpenSpec changes")

                # Render and return the changes list
                rendered = await render_openspec_template(self._session, "_list-format")
                if rendered:
                    return EventResult(
                        result=True,
                        message=f"File content cached for {path_name}",
                        rendered_content=rendered,
                    )
                return None

            elif path_name == ".openspec-show.json":
                # Cache the show data
                self._activation.set_cached_data("openspec_show", json_data)

                # Render and return the show format
                rendered = await render_openspec_template(
                    self._session, "_show-format", extra_context=TemplateContext(json_data)
                )
                if rendered:
                    return EventResult(
                        result=True,
                        message=f"File content cached for {path_name}",
                        rendered_content=rendered,
                    )
                return None

        return None

    async def _parse_detection(self, version_output: str | None) -> None:
        """Parse a combined OpenSpec detection response and store global state.

        Args:
            version_output: Output from ``openspec --version``, if it ran.
        """
        try:
            self._available = version_output is not None
            self._activation.set_cached_data("openspec_available", self._available)
            # Extract semantic version (e.g., "1.2.3" or "v1.2.3")
            match = re.search(r"v?(\d+\.\d+\.\d+)", version_output or "")
            if match:
                self._version = match.group(1)
                self._version_this_session = self._version
                self._activation.set_cached_data("openspec_version", self._version)
                logger.info(f"OpenSpec version: {self._version}")

                await self._persist_global_state(validated=True, version=self._version)

                # CLI state is global, but OpenSpec project detection is local.
                if not self._project_requested:
                    self._project_requested = True
                    await self.request_project_check()
            else:
                logger.warning(f"Failed to parse OpenSpec version from: {version_output}")
                self._version = None
                self._version_this_session = None
                self._activation.set_cached_data("openspec_version", None)
                await self._persist_global_state(validated=False)
        finally:
            # Always acknowledge to prevent re-queuing.
            if self._detection_instruction_id:
                await self._activation.acknowledge_instruction(self._detection_instruction_id)
                self._detection_instruction_id = None

    async def _format_error_response(self, data: dict[str, Any]) -> RenderedContent | None:
        """Format OpenSpec CLI error using template.

        Args:
            data: Parsed JSON with error fields

        Returns:
            RenderedContent with formatted content, or None if filtered by requires-*
        """
        return await render_openspec_template(self._session, "_error-format", extra_context=TemplateContext(data))
