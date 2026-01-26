"""OpenSpec CLI detection task."""

import re
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_OPENSPEC
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.rendering import render_common_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)

# Cache and timer constants
CHANGES_CACHE_TTL = 3600  # 1 hour
CHANGES_CHECK_INTERVAL = 3600.0  # 60 minutes
CHANGES_CHECK_START_DELAY = 20.0  # 20 seconds


@task_init
class OpenSpecTask:
    """Task for detecting OpenSpec CLI availability."""

    def __init__(self, task_manager: Optional["TaskManager"] = None):
        if task_manager is None:
            task_manager = get_task_manager()
        self.task_manager = task_manager
        self._cli_requested = False
        self._flag_checked = False
        self._available: Optional[bool] = None
        self._project_requested = False
        self._project_enabled: Optional[bool] = None
        self._version_requested = False
        self._version: Optional[str] = None
        self._changes_requested = False
        self._changes_cache: Optional[list[dict[str, Any]]] = None
        self._changes_timestamp: Optional[float] = None
        self._changes_timer_started = False  # Track if first timer has fired

        # Subscribe to command and file events
        self.task_manager.subscribe(self, EventType.FS_COMMAND | EventType.FS_DIRECTORY | EventType.FS_FILE_CONTENT)

        # Subscribe to timer for periodic changes monitoring with start delay
        self.task_manager.subscribe(self, EventType.TIMER, CHANGES_CHECK_INTERVAL, CHANGES_CHECK_START_DELAY)

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "OpenSpecTask"

    async def on_tool(self) -> None:
        """Called after tool/prompt execution.

        Flag checking is now handled in on_init() at server startup.
        """
        pass

    async def on_init(self) -> None:
        """Initialize task at server startup.

        Checks if OpenSpec is enabled via flags and unsubscribes if disabled.
        """
        if not self.task_manager.requires_flag(FLAG_OPENSPEC):
            await self.task_manager.unsubscribe(self)
            logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
            self._flag_checked = True
            return

        # Request CLI availability check
        if not self._cli_requested:
            await self.request_cli_check()
            self._cli_requested = True
        self._flag_checked = True

    def is_available(self) -> Optional[bool]:
        """Check if OpenSpec CLI is available.

        Returns:
            True if available, False if not available, None if not yet checked.
        """
        return self._available

    def is_project_enabled(self) -> Optional[bool]:
        """Check if OpenSpec project is initialized.

        Returns:
            True if project initialized, False if not, None if not yet checked.
        """
        return self._project_enabled

    def get_version(self) -> Optional[str]:
        """Get OpenSpec CLI version.

        Returns:
            Version string (e.g., "1.2.3") or None if not available.
        """
        return self._version

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
        content = await render_common_template("openspec-cli-check")
        await self.task_manager.queue_instruction(content)

    async def request_project_check(self) -> None:
        """Request OpenSpec project structure check from client."""
        content = await render_common_template("openspec-project-check")
        await self.task_manager.queue_instruction(content)

    async def request_version_check(self) -> None:
        """Request OpenSpec CLI version from client."""
        content = await render_common_template("openspec-version-check")
        await self.task_manager.queue_instruction(content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "bool | Result[Any]":
        """Handle task manager events."""
        # Handle timer events for changes monitoring
        if event_type & EventType.TIMER:
            interval = data.get("interval")
            if interval == CHANGES_CHECK_INTERVAL:
                # Skip first timer event (respects start delay configured in subscribe)
                if not self._changes_timer_started:
                    self._changes_timer_started = True
                    return True
                await self._handle_changes_reminder()
                return True

        # Handle command location events
        if event_type & EventType.FS_COMMAND:
            command = data.get("command")
            if command == "openspec":
                path = data.get("path", "")
                found = data.get("found", False)
                self._available = found and bool(path)
                self.task_manager.set_cached_data("openspec_available", self._available)
                logger.info(f"OpenSpec CLI {'available' if self._available else 'not available'}")

                # If CLI available, check project structure
                if self._available and not self._project_requested:
                    self._project_requested = True
                    await self.request_project_check()

                return True

        # Handle file content events
        if event_type & EventType.FS_FILE_CONTENT:
            import json
            from pathlib import Path

            path = data.get("path", "")
            path_name = Path(path).name

            # Handle project detection
            if path_name == "project.md" and path.startswith("openspec/"):
                # If project.md exists, project is enabled
                self._project_enabled = True
                self.task_manager.set_cached_data("openspec_project_enabled", True)
                logger.info("OpenSpec project enabled")

                # Request version and changes
                if not self._version_requested:
                    self._version_requested = True
                    await self.request_version_check()
                if not self._changes_requested:
                    self._changes_requested = True
                    await self.request_changes_json()

                return True

            # Handle version detection
            if path_name == ".openspec-version.txt":
                content = data.get("content", "")
                self._parse_version(content)
                return True

            # Handle OpenSpec command responses
            content = data.get("content", "")

            # Parse JSON responses
            try:
                json_data = json.loads(content)
            except json.JSONDecodeError:
                logger.debug(f"Non-JSON content in {path_name}, skipping")
                return False

            # Check for error responses first
            if "error" in json_data:
                formatted = await self._format_error_response(json_data)
                await self.task_manager.queue_instruction(formatted)
                return True

            # Format specific OpenSpec responses
            if path_name == ".openspec-status.json":
                formatted = await self._format_status_response(json_data)
                await self.task_manager.queue_instruction(formatted)
                return True

            elif path_name == ".openspec-changes.json":
                # Cache the changes data
                import time

                changes = json_data.get("changes", [])
                self._changes_cache = changes
                self._changes_timestamp = time.time()
                self.task_manager.set_cached_data("openspec_changes", changes)
                logger.debug(f"Cached {len(changes)} OpenSpec changes")

                # Invalidate template context cache to pick up fresh changes
                from mcp_guide.utils.template_context_cache import invalidate_template_context_cache

                invalidate_template_context_cache()
                logger.debug("Template context cache invalidated after OpenSpec changes update")

                # Render and return the changes list as a Result
                from mcp_guide.result import Result

                formatted = await render_common_template("_openspec-list-format")
                return Result.ok(value=formatted, message=f"File content cached for {path_name}", instruction="")

            elif path_name == ".openspec-show.json":
                formatted = await self._format_show_response(json_data)
                await self.task_manager.queue_instruction(formatted)
                return True

        return False

    async def request_changes_json(self) -> None:
        """Request openspec changes JSON via command execution."""
        content = await render_common_template("_commands/openspec/list")
        await self.task_manager.queue_instruction(content)

    async def _handle_changes_reminder(self) -> None:
        """Handle timer events for changes monitoring."""
        if not self._project_enabled:
            return

        # Only remind if cache is stale
        if not self.is_cache_valid():
            try:
                await self.request_changes_json()
                logger.trace("Queued OpenSpec changes refresh")
            except Exception as e:
                logger.warning(f"Failed to queue OpenSpec changes refresh: {e}")

    def _parse_version(self, content: str) -> None:
        """Parse OpenSpec version from command output.

        Args:
            content: Output from openspec --version command
        """
        # Extract semantic version (e.g., "1.2.3" or "v1.2.3")
        match = re.search(r"v?(\d+\.\d+\.\d+)", content)
        if match:
            self._version = match.group(1)
            self.task_manager.set_cached_data("openspec_version", self._version)
            logger.info(f"OpenSpec version: {self._version}")
        else:
            logger.warning(f"Failed to parse OpenSpec version from: {content}")
            self._version = None
            self.task_manager.set_cached_data("openspec_version", None)

    async def _format_status_response(self, data: dict[str, Any]) -> str:
        """Format OpenSpec status response using template.

        Args:
            data: Parsed JSON from openspec status command

        Returns:
            Formatted markdown string
        """
        return await render_common_template("_commands/openspec/_status-format", extra_context=data)

    async def _format_changes_list_response(self, data: dict[str, Any]) -> str:
        """Format OpenSpec changes list response using template.

        Args:
            data: Parsed JSON from openspec list command

        Returns:
            Formatted markdown string
        """
        changes = data.get("changes", [])

        # Sort: in-progress first, then by last modified (newest first)
        # Step 1: Sort by lastModified descending (newest first)
        # Step 2: Stable sort by status to put in-progress first
        sorted_changes = sorted(changes, key=lambda c: c.get("lastModified", ""), reverse=True)
        sorted_changes = sorted(sorted_changes, key=lambda c: c.get("status") != "in-progress")

        # Add formatted fields for template
        for change in sorted_changes:
            completed = change.get("completedTasks", 0)
            total = change.get("totalTasks", 0)
            change["progress"] = f"{completed}/{total}" if total > 0 else "N/A"
            last_mod = change.get("lastModified", "")
            change["lastModified"] = last_mod[:10] if last_mod else "N/A"

        context = {"has_changes": len(sorted_changes) > 0, "sorted_changes": sorted_changes}
        return await render_common_template("_commands/openspec/_changes-format", extra_context=context)

    async def _format_show_response(self, data: dict[str, Any]) -> str:
        """Format OpenSpec show response using template.

        Args:
            data: Parsed JSON from openspec show command

        Returns:
            Formatted markdown string
        """
        return await render_common_template("_commands/openspec/_show-format", extra_context=data)

    async def _format_error_response(self, data: dict[str, Any]) -> str:
        """Format OpenSpec CLI error using template.

        Args:
            data: Parsed JSON with error fields

        Returns:
            Formatted markdown string
        """
        return await render_common_template("_commands/openspec/_error-format", extra_context=data)
