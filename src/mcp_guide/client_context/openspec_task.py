"""OpenSpec CLI detection task."""

import re
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_OPENSPEC
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.rendering import render_common_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)


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

        # Subscribe to startup and command events
        self.task_manager.subscribe(
            self, EventType.TIMER_ONCE | EventType.FS_COMMAND | EventType.FS_DIRECTORY | EventType.FS_FILE_CONTENT, 5.0
        )

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "OpenSpecTask"

    async def on_tool(self) -> None:
        """Check flag and unsubscribe if disabled."""
        if self._flag_checked:
            return

        self._flag_checked = True

        try:
            from mcp_guide.session import get_or_create_session
            from mcp_guide.utils.flag_utils import get_resolved_flag_value

            session = await get_or_create_session()
            enabled = await get_resolved_flag_value(session, FLAG_OPENSPEC, False)

            if not enabled:
                await self.task_manager.unsubscribe(self)
                logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
        except Exception as e:
            logger.warning(f"Failed to check openspec flag, unsubscribing: {e}")
            await self.task_manager.unsubscribe(self)

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

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        # Handle TIMER_ONCE startup
        if event_type & EventType.TIMER_ONCE:
            # Wait for flag check before proceeding
            if not self._flag_checked:
                return False  # Requeue until on_tool is called

            if not self._cli_requested:
                await self.request_cli_check()
                self._cli_requested = True
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

        # Handle directory listing events for project detection
        if event_type & EventType.FS_DIRECTORY:
            path = data.get("path", "")
            if path.rstrip("/") == "openspec":
                # FS_DIRECTORY events use "files" key from send_directory_listing
                entries = data.get("files", [])
                self._check_project_structure(entries)

                # If project enabled, request version
                if self._project_enabled and not self._version_requested:
                    self._version_requested = True
                    await self.request_version_check()

                return True

        # Handle file content events for version detection
        if event_type & EventType.FS_FILE_CONTENT:
            path = data.get("path", "")
            if path == ".openspec-version.txt":
                content = data.get("content", "")
                self._parse_version(content)
                return True

        return False

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

    def _check_project_structure(self, entries: list[dict[str, Any]]) -> None:
        """Check if OpenSpec project structure is valid.

        Args:
            entries: Directory listing entries from openspec/ directory
        """
        # Check for required files and directories
        has_project_md = False
        has_changes_dir = False
        has_specs_dir = False

        for entry in entries:
            name = entry.get("name", "")
            entry_type = entry.get("type", "")

            if name == "project.md" and entry_type == "file":
                has_project_md = True
            elif name == "changes" and entry_type == "directory":
                has_changes_dir = True
            elif name == "specs" and entry_type == "directory":
                has_specs_dir = True

        self._project_enabled = has_project_md and has_changes_dir and has_specs_dir
        self.task_manager.set_cached_data("openspec_project_enabled", self._project_enabled)
        logger.info(f"OpenSpec project {'enabled' if self._project_enabled else 'not initialized'}")
