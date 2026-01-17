"""Workflow-specific task implementations."""

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.models import FileReadError, NoProjectError
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.change_detection import ChangeEvent, detect_workflow_changes
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_FILE
from mcp_guide.workflow.instruction_generator import get_instruction_template_for_change
from mcp_guide.workflow.parser import parse_workflow_state
from mcp_guide.workflow.rendering import render_workflow_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)

# Workflow monitoring interval in seconds
WORKFLOW_INTERVAL = 600.0  # 10 minutes

# OpenSpec monitoring interval in seconds
OPENSPEC_INTERVAL = 3600.0  # 60 minutes

# Cache TTL for openspec changes list (24 hours)
OPENSPEC_CACHE_TTL = 86400.0  # 24 hours in seconds

# OpenSpec directory structure
OPENSPEC_DIR = "openspec"
OPENSPEC_CHANGES_DIR = "changes"


@task_init
class WorkflowMonitorTask:
    """Scheduled background monitoring task for workflow state changes."""

    # noinspection PyMethodMayBeStatic
    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "WorkflowMonitorTask"

    def __init__(
        self,
        workflow_file_path: Optional[str] = None,
    ):
        # Use default workflow file if none provided
        if workflow_file_path is None:
            workflow_file_path = str(DEFAULT_WORKFLOW_FILE)

        self.workflow_file_path = workflow_file_path

        # Get the singleton TaskManager
        self.task_manager: "TaskManager" = get_task_manager()

        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None
        self._setup_done = False
        self._last_openspec_reminder: float = 0.0

        # Subscribe self to task manager for workflow monitoring
        self.task_manager.subscribe(self, EventType.TIMER | EventType.FS_FILE_CONTENT, WORKFLOW_INTERVAL)

        # Subscribe for OpenSpec monitoring reminders
        self.task_manager.subscribe(self, EventType.TIMER, OPENSPEC_INTERVAL)

        # Subscribe for directory listing events
        self.task_manager.subscribe(self, EventType.FS_DIRECTORY)

    async def on_tool(self) -> None:
        """Called after tool/prompt execution."""
        logger.trace(f"WorkflowMonitorTask.on_tool called, _setup_done={self._setup_done}")
        if not self._setup_done:
            try:
                content = await render_workflow_template("monitoring-setup")
                await self.task_manager.queue_instruction(content)
                self._setup_done = True
                logger.trace("WorkflowMonitorTask.on_tool: Queued setup instruction")
            except Exception as e:
                logger.warning(f"Failed to queue workflow setup: {e}")

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        logger.trace(f"WorkflowMonitorTask received event: {event_type} for path: {data.get('path', 'unknown')}")

        # Handle timer events
        if event_type & EventType.TIMER:
            interval = data.get("interval")

            # OpenSpec monitoring reminder (60 min interval)
            if interval == OPENSPEC_INTERVAL:
                await self._handle_openspec_reminder()
                return True

            # Workflow monitoring reminder (2 min interval)
            if interval == WORKFLOW_INTERVAL:
                await self._handle_monitoring_reminder()
                return True

        # Handle directory listing for openspec/changes
        if event_type & EventType.FS_DIRECTORY:
            path = data.get("path", "")
            if path == f"{OPENSPEC_DIR}/{OPENSPEC_CHANGES_DIR}":
                self._handle_openspec_changes_listing(data.get("files", []))
                return True

        # Check if the file content is for our workflow file (compare basenames)
        path = data.get("path")
        if isinstance(path, str) and Path(path).name == Path(self.workflow_file_path).name:
            # Process the data
            await self._process_workflow_content(data.get("content", ""))
            return True
        return False

    async def _handle_monitoring_reminder(self) -> None:
        """Handle timer events for workflow monitoring reminders."""
        try:
            content = await render_workflow_template("monitoring-reminder")
            await self.task_manager.queue_instruction(content)
        except (NoProjectError, FileReadError) as e:
            logger.warning(f"Monitoring reminder failed due to configuration issue: {e}")
        except Exception as e:
            logger.error(f"Failed to queue monitoring reminder: {e}", exc_info=True)

    async def _handle_openspec_reminder(self) -> None:
        """Handle timer events for OpenSpec monitoring reminders."""
        try:
            content = await render_workflow_template("openspec-changes-check")
            await self.task_manager.queue_instruction(content)
            self._last_openspec_reminder = time.time()
            logger.trace("Queued OpenSpec changes check reminder")
        except (NoProjectError, FileReadError) as e:
            logger.warning(f"OpenSpec reminder failed due to configuration issue: {e}")
        except Exception as e:
            logger.error(f"Failed to queue OpenSpec reminder: {e}", exc_info=True)

    def _handle_openspec_changes_listing(self, entries: list[dict[str, Any]]) -> None:
        """Handle openspec/changes directory listing from client.

        Args:
            entries: List of directory entries with 'name' and 'type' fields from send_directory_listing
        """
        # Extract directory names (filter out files)
        changes_list = [entry["name"] for entry in entries if entry.get("type") == "directory"]
        self.task_manager.set_cached_data("openspec_changes_list", changes_list)
        self.task_manager.set_cached_data("openspec_changes_timestamp", time.time())
        logger.trace(f"Cached {len(changes_list)} openspec changes: {changes_list}")

    async def _process_workflow_content(self, content: str) -> None:
        """Process workflow file content and update cached state."""
        logger.trace("_process_workflow_content called")
        try:
            new_state = parse_workflow_state(content)
            if not new_state:
                logger.warning("Failed to parse workflow state - not processing changes")
                return

            logger.trace(f"Parsed new workflow state: phase={new_state.phase}, issue={new_state.issue}")

            # Get previous state from cache for comparison
            old_state = self.task_manager.get_cached_data("workflow_state")
            logger.trace(f"Retrieved old state from cache: {old_state is not None}")

            # Detect semantic changes
            changes = detect_workflow_changes(old_state, new_state)
            logger.trace(f"Detected {len(changes)} workflow changes")

            # Process each detected change and get rendered content for main response
            if changes:
                change_content = await self._process_workflow_changes(changes)
                if change_content:
                    # Store the change content to be used as the main response value
                    self.task_manager.set_cached_data("workflow_change_content", change_content)

            # Always queue monitoring instruction after successful parse (maintains original behaviour)
            # This ensures the critical "MUST send file content" instruction is always provided
            try:
                content = await render_workflow_template("monitoring-result")
                await self.task_manager.queue_instruction(content)
            except (NoProjectError, FileReadError) as e:
                logger.warning(f"Monitoring result failed due to configuration issue: {e}")
            except Exception as e:
                logger.error(f"Failed to queue monitoring result instruction: {e}", exc_info=True)

            # Update cache with new state AFTER processing changes
            self.task_manager.set_cached_data("workflow_state", new_state)
            logger.trace("New workflow state cached in TaskManager")

            # Check if issue changed - if so, request fresh openspec changes listing
            if old_state and old_state.issue != new_state.issue:
                logger.trace(f"Issue changed from {old_state.issue} to {new_state.issue}, requesting openspec refresh")
                asyncio.create_task(self._request_openspec_changes_listing())

            # Detect OpenSpec change by checking cached directory listing
            is_openspec = self._detect_openspec_change(new_state.issue)
            self.task_manager.set_cached_data("openspec_current_change", is_openspec)
            logger.trace(f"OpenSpec change detection: {is_openspec}")

        except Exception as e:
            logger.error(f"Failed to process workflow content: {e}", exc_info=True)

    def _detect_openspec_change(self, issue_name: Optional[str]) -> bool:
        """Check if issue matches OpenSpec change by checking cached directory listing.

        Args:
            issue_name: Current issue name from workflow state

        Returns:
            True if issue name exists in cached openspec/changes/ directory listing
        """
        if not issue_name:
            return False

        # Get cached directory listing and timestamp
        changes_list = self.task_manager.get_cached_data("openspec_changes_list")
        cache_timestamp = self.task_manager.get_cached_data("openspec_changes_timestamp")

        # Check if cache is expired (24 hours)
        cache_expired = False
        if cache_timestamp:
            age = time.time() - cache_timestamp
            cache_expired = age > OPENSPEC_CACHE_TTL
            if cache_expired:
                logger.trace(f"OpenSpec cache expired (age: {age:.0f}s)")

        if not changes_list or cache_expired:
            # Request directory listing if not cached or expired
            asyncio.create_task(self._request_openspec_changes_listing())
            return False

        # Check if issue_name is in the cached list
        return issue_name in changes_list

    async def _request_openspec_changes_listing(self) -> None:
        """Request openspec/changes directory listing from client."""
        try:
            content = await render_workflow_template("openspec-changes-check")
            await self.task_manager.queue_instruction(content)
        except Exception as e:
            logger.warning(f"Failed to request openspec changes listing: {e}")

    @staticmethod
    async def _process_workflow_changes(changes: list[ChangeEvent]) -> Optional[str]:
        """Process detected workflow changes and return rendered content for main response.

        Returns:
            Rendered change content for main response, or None if no content to return
        """
        # Process each change using existing workflow instruction system
        rendered_contents = []
        for change in changes:
            logger.trace(f"Processing change: {change.change_type.value}")

            # Get appropriate template pattern for this change
            template_pattern = get_instruction_template_for_change(change)

            # Render template content for main response
            try:
                content = await render_workflow_template(template_pattern)
                rendered_contents.append(content)
                logger.trace(
                    f"Rendered workflow content for {change.change_type.value} using pattern: {template_pattern}"
                )
            except (NoProjectError, FileReadError) as e:
                logger.warning(f"Template rendering failed for {template_pattern}: {e}")
            except Exception as e:
                logger.error(f"Failed to render template {template_pattern}: {e}", exc_info=True)

        # Combine all rendered content
        return "\n".join(rendered_contents) if rendered_contents else None
