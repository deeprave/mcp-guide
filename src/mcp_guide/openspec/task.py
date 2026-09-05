"""OpenSpec CLI detection task."""

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
    from mcp_guide.task_manager import TaskManager
    from mcp_guide.task_manager.manager import EventResult

logger = get_logger(__name__)

# Cache and timer constants
CHANGES_CACHE_TTL = 3600  # 1 hour
CHANGES_CHECK_INTERVAL = 3600.0  # 60 minutes
OPENSPEC_CHECK_INTERVAL = 24 * 60 * 60


@task_register
class OpenSpecTask(InitialisableMixin):
    """Task for detecting OpenSpec CLI availability."""

    def __init__(self, task_manager: "TaskManager"):
        """Create a project task with its owning Session's manager."""
        self.task_manager = task_manager
        self._session: Any = task_manager._session
        self._cli_requested = False
        self._flag_checked = False
        self._available: Optional[bool] = None
        self._project_requested = False
        self._project_enabled: Optional[bool] = None
        self._version_requested = False
        self._version: Optional[str] = None
        self._version_this_session: Optional[str] = None  # Session-level cache
        self._changes_requested = False
        self._changes_cache: Optional[list[dict[str, Any]]] = None
        self._changes_timestamp: Optional[float] = None

        # Instruction tracking IDs
        self._cli_instruction_id: Optional[str] = None
        self._project_instruction_id: Optional[str] = None
        self._version_instruction_id: Optional[str] = None
        self._changes_instruction_id: Optional[str] = None

    async def start(self, task_manager: "TaskManager", session: Any) -> bool:
        """Start OpenSpec detection if enabled for the current project."""
        self.task_manager = task_manager
        self._session = session
        if not await self._is_enabled():
            logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
            self._flag_checked = True
            return False

        task_manager.subscribe(
            self,
            EventType.FS_COMMAND | EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY | EventType.TIMER,
            CHANGES_CHECK_INTERVAL,
            once_interval=DEFAULT_ONCE_INTERVAL,
        )
        return True

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
            await self.task_manager.unsubscribe(self)
            logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
            self._flag_checked = True
            return EventResult(result=True)

        state = await self._get_global_state()
        if self._is_recent(state):
            self._available = state.validated
            self._version = state.version
            self.task_manager.set_cached_data("openspec_available", self._available)
            self.task_manager.set_cached_data("openspec_version", self._version)
            if state.validated and not self._project_requested:
                self._project_requested = True
                await self.request_project_check()
        elif not self._cli_requested:
            await self.request_cli_check()
            self._cli_requested = True
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

    def meets_minimum_version(self, minimum: str) -> bool:
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
        data = self.task_manager.get_cached_data("openspec_show")
        return data if isinstance(data, dict) else None

    def get_status(self) -> Optional[dict[str, Any]]:
        """Get cached OpenSpec status data.

        Returns:
            Status data dict or None if not cached.
        """
        data = self.task_manager.get_cached_data("openspec_status")
        return data if isinstance(data, dict) else None

    def is_cache_valid(self, ttl: int = CHANGES_CACHE_TTL) -> bool:
        """Check if changes cache is valid.

        Args:
            ttl: Time-to-live in seconds (default: CHANGES_CACHE_TTL)

        Returns:
            True if cache exists and is not expired, False otherwise.
        """
        if self._changes_cache is None or self._changes_timestamp is None:
            return False

        import time

        age = time.time() - self._changes_timestamp
        return age < ttl

    async def request_cli_check(self) -> None:
        """Request OpenSpec CLI availability check from client."""
        rendered = await render_openspec_template(self._session, "openspec-cli-check")
        if rendered:
            self._cli_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)

    async def request_project_check(self) -> None:
        """Request OpenSpec project structure check from client."""
        rendered = await render_openspec_template(self._session, "openspec-project-check")
        if rendered:
            self._project_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)

    async def request_version_check(self) -> None:
        """Request OpenSpec CLI version from client."""
        rendered = await render_openspec_template(self._session, "openspec-version-check")
        if rendered:
            self._version_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        """Handle task manager events."""
        from mcp_guide.task_manager.manager import EventResult

        if result := await self._handle_timer_once(event_type):
            return result

        # Handle timer events for changes monitoring
        if event_type & EventType.TIMER:
            interval = data.get("interval")
            if interval == CHANGES_CHECK_INTERVAL:
                await self._handle_changes_reminder()
                return EventResult(result=True)

        # Handle command location events
        if event_type & EventType.FS_COMMAND:
            command = data.get("command")
            if command == "openspec":
                path = data.get("path", "")
                found = data.get("found", False)
                self._available = found and bool(path)
                self.task_manager.set_cached_data("openspec_available", self._available)
                logger.info(f"OpenSpec CLI {'available' if self._available else 'not available'}")

                # Acknowledge CLI check instruction
                if self._cli_instruction_id:
                    await self.task_manager.acknowledge_instruction(self._cli_instruction_id)
                    self._cli_instruction_id = None

                # If CLI available, request version check first
                if self._available and not self._version_requested:
                    self._version_requested = True
                    await self.request_version_check()
                elif not self._available:
                    await self._persist_global_state(validated=False)

                return EventResult(result=True)

        # Handle directory listing events
        if event_type & EventType.FS_DIRECTORY:
            path = data.get("path", "")
            if path == "openspec":
                files = data.get("files", [])
                self._project_enabled = any(f.get("name") == "config.yaml" for f in files)

                # Acknowledge project check instruction
                if self._project_instruction_id:
                    await self.task_manager.acknowledge_instruction(self._project_instruction_id)
                    self._project_instruction_id = None

                if self._project_enabled:
                    # Request changes list after validation
                    if not self._changes_requested:
                        self._changes_requested = True
                        await self.request_changes_json()

                return EventResult(result=True)
            return None

        # Handle file content events
        if event_type & EventType.FS_FILE_CONTENT:
            import json
            from pathlib import Path

            path = data.get("path", "")
            path_name = Path(path).name

            # Handle version detection
            if path_name == ".openspec-version.txt":
                content = data.get("content", "")
                await self._parse_version(content)

                # Acknowledge version check instruction
                if self._version_instruction_id:
                    await self.task_manager.acknowledge_instruction(self._version_instruction_id)
                    self._version_instruction_id = None

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
                self.task_manager.set_cached_data("openspec_status", json_data)

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
                self.task_manager.set_cached_data("openspec_changes", changes)
                logger.debug(f"Cached {len(changes)} OpenSpec changes")

                # Acknowledge changes request instruction
                if self._changes_instruction_id:
                    await self.task_manager.acknowledge_instruction(self._changes_instruction_id)
                    self._changes_instruction_id = None

                # Invalidate template context cache to pick up fresh changes
                from mcp_guide.render.cache import invalidate_template_context_cache

                invalidate_template_context_cache(self._session)
                logger.debug("Template context cache invalidated after OpenSpec changes update")

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
                self.task_manager.set_cached_data("openspec_show", json_data)

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

    async def request_changes_json(self) -> None:
        """Request openspec changes JSON via command execution."""
        rendered = await render_openspec_template(self._session, "openspec-get-changes")
        if rendered:
            self._changes_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)

    async def _handle_changes_reminder(self) -> None:
        """Handle timer events for changes monitoring.

        Invalidates cache when TTL expires. Data will be fetched on-demand
        when :openspec/list command is next invoked.
        """
        if not self.is_cache_valid():
            self._changes_timestamp = None
            logger.trace("OpenSpec changes cache invalidated")

    async def _parse_version(self, content: str) -> None:
        """Parse OpenSpec version from command output and store global state.

        Args:
            content: Output from openspec --version command
        """
        try:
            # Extract semantic version (e.g., "1.2.3" or "v1.2.3")
            match = re.search(r"v?(\d+\.\d+\.\d+)", content)
            if match:
                self._version = match.group(1)
                self._version_this_session = self._version
                self.task_manager.set_cached_data("openspec_version", self._version)
                logger.info(f"OpenSpec version: {self._version}")

                await self._persist_global_state(validated=True, version=self._version)

                # CLI state is global, but OpenSpec project detection is local.
                if not self._project_requested:
                    self._project_requested = True
                    await self.request_project_check()
            else:
                logger.warning(f"Failed to parse OpenSpec version from: {content}")
                self._version = None
                self._version_this_session = None
                self.task_manager.set_cached_data("openspec_version", None)
                await self._persist_global_state(validated=False)
        finally:
            # Always acknowledge to prevent re-queuing
            if self._version_instruction_id:
                await self.task_manager.acknowledge_instruction(self._version_instruction_id)
                self._version_instruction_id = None

    async def _format_error_response(self, data: dict[str, Any]) -> RenderedContent | None:
        """Format OpenSpec CLI error using template.

        Args:
            data: Parsed JSON with error fields

        Returns:
            RenderedContent with formatted content, or None if filtered by requires-*
        """
        return await render_openspec_template(self._session, "_error-format", extra_context=TemplateContext(data))
