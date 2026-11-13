"""Workflow-specific task implementations."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_register
from mcp_guide.feature_flags.constants import FLAG_WORKFLOW, FLAG_WORKFLOW_FILE
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.protocol import DEFAULT_ONCE_INTERVAL, InitialisableMixin
from mcp_guide.workflow.change_detection import ChangeEvent, detect_workflow_changes
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_FILE
from mcp_guide.workflow.instruction_generator import get_instruction_template_for_change
from mcp_guide.workflow.parser import WorkflowStateValidationError, parse_workflow_state
from mcp_guide.workflow.rendering import render_workflow_template

if TYPE_CHECKING:
    from mcp_guide.render.content import RenderedContent
    from mcp_guide.task_manager.activation import TaskActivation
    from mcp_guide.task_manager.manager import EventResult

logger = get_logger(__name__)

# Workflow monitoring interval in seconds
WORKFLOW_INTERVAL = 600.0  # 10 minutes


@task_register
class WorkflowMonitorTask(InitialisableMixin):
    """Scheduled background monitoring task for workflow state changes."""

    configuration_flags = frozenset({FLAG_WORKFLOW, FLAG_WORKFLOW_FILE})

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

        self.activation: TaskActivation | None = None
        self._session: Any = None

        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None
        self._setup_done = False
        self._uses_linked_worktree_minimum = False

        # Instruction tracking IDs
        self._setup_instruction_id: Optional[str] = None
        self._reminder_instruction_id: Optional[str] = None

    async def start(self, activation: "TaskActivation") -> bool:
        """Start workflow monitoring if workflow is enabled for the current project."""
        self.activation = activation
        self._session = activation.session
        if await activation.requires_flag(FLAG_WORKFLOW):
            self._uses_linked_worktree_minimum = False
        elif self._is_linked_worktree_session():
            self._uses_linked_worktree_minimum = True
        else:
            logger.debug(f"WorkflowMonitorTask disabled - {FLAG_WORKFLOW} flag not set")
            return False

        workflow_file = (await activation.resolved_flags()).get(FLAG_WORKFLOW_FILE)
        if workflow_file and isinstance(workflow_file, str):
            self.workflow_file_path = workflow_file
            activation.set_cached_data("workflow_file_path", workflow_file)
            logger.debug(f"WorkflowMonitorTask using workflow file from flag: {workflow_file}")

        activation.subscribe(
            EventType.TIMER | EventType.FS_FILE_CONTENT,
            WORKFLOW_INTERVAL,
            15.0,
            once_interval=DEFAULT_ONCE_INTERVAL,
        )
        return True

    async def on_tool(self) -> None:
        pass

    async def _initialise(self) -> "EventResult":
        """Check flag and queue setup instruction if enabled."""
        from mcp_guide.task_manager.manager import EventResult

        if self._session is None:
            return EventResult(result=False, message="Workflow task is not attached to a Session")
        if self.activation is None:
            return EventResult(result=False, message="Workflow task has no activation")
        workflow_enabled = await self._workflow_enabled_for_session()

        if not workflow_enabled:
            await self.activation.unsubscribe()
            logger.debug(f"WorkflowMonitorTask disabled - {FLAG_WORKFLOW} flag not set")
            return EventResult(result=True)

        if not self._setup_done:
            rendered = await render_workflow_template(self._session, "monitoring-setup")
            if rendered:
                self._setup_instruction_id = await self.activation.queue_instruction_with_ack(rendered.content)
            self._setup_done = True
            logger.debug("WorkflowMonitorTask initialized")
        return EventResult(result=True)

    async def _workflow_enabled_for_session(self) -> bool:
        """Allow a linked session to receive its initial local workflow file."""
        if self.activation is None:
            return False
        return await self.activation.requires_flag(FLAG_WORKFLOW) or self._uses_linked_worktree_minimum

    def _is_linked_worktree_session(self) -> bool:
        """Return whether the bound session targets a linked worktree."""
        if self.activation is None:
            return False
        session = self.activation.session
        return session.worktree_path is not None and session.worktree_path != session.bound_root_path

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> "EventResult | None":
        """Handle task manager events."""
        from mcp_guide.task_manager.manager import EventResult

        logger.trace(f"WorkflowMonitorTask received event: {event_type} for path: {data.get('path', 'unknown')}")

        if result := await self._handle_timer_once(event_type):
            return result

        # Handle timer events
        if event_type & EventType.TIMER:
            interval = data.get("timer_interval")

            # Workflow monitoring reminder (10 min interval)
            if interval == WORKFLOW_INTERVAL:
                await self._handle_monitoring_reminder()
                return EventResult(result=True)

        # Match the configured workflow filename regardless of whether the
        # client reports its full path or only its basename.  The receiving
        # Session owns the worktree association.
        path = data.get("path")
        workflow_basename = Path(self.workflow_file_path).name
        if isinstance(path, str) and Path(path).name == workflow_basename:
            try:
                rendered_content = await self._process_workflow_content(data.get("content", ""))
            except WorkflowStateValidationError as error:
                return EventResult(result=False, message=str(error))

            await self._acknowledge_pending_instructions()
            return EventResult(result=True, rendered_content=rendered_content)
        return None

    async def _acknowledge_pending_instructions(self) -> None:
        """Acknowledge setup and reminder guidance after a valid submission."""
        for attribute in ("_setup_instruction_id", "_reminder_instruction_id"):
            instruction_id = getattr(self, attribute)
            if instruction_id and self.activation is not None:
                await self.activation.acknowledge_instruction(instruction_id)
            setattr(self, attribute, None)

    async def _handle_monitoring_reminder(self) -> None:
        """Handle timer events for workflow monitoring reminders."""
        rendered = await render_workflow_template(self._session, "monitoring-reminder")
        if rendered:
            if self.activation is not None:
                self._reminder_instruction_id = await self.activation.queue_instruction_with_ack(rendered.content)

    async def _process_workflow_content(self, content: str) -> Optional["RenderedContent"]:
        """Process workflow file content and update cached state."""
        logger.trace("_process_workflow_content called")
        try:
            new_state = parse_workflow_state(content, raise_validation_error=True)
            if not new_state:
                logger.warning("Failed to parse workflow state - not processing changes")
                return None

            expected_worktree = self._session.worktree_name if self._session is not None else None
            if expected_worktree is None:
                if new_state.worktree is None:
                    raise WorkflowStateValidationError(
                        "Invalid workflow file: linked worktree must provide a `worktree` label"
                    )
                try:
                    self._session.adopt_worktree_name(new_state.worktree)
                except ValueError as error:
                    raise WorkflowStateValidationError(str(error)) from error
            elif expected_worktree == "root":
                if new_state.worktree not in (None, "root"):
                    raise WorkflowStateValidationError(
                        f"Invalid workflow file: worktree `{new_state.worktree}` does not match `root`"
                    )
            elif new_state.worktree is None:
                raise WorkflowStateValidationError(
                    f"Invalid workflow file: worktree must be `{expected_worktree}` for this session"
                )
            elif new_state.worktree != expected_worktree:
                if self.activation is None or self.activation.get_cached_data("workflow_state") is not None:
                    raise WorkflowStateValidationError(
                        f"Invalid workflow file: worktree must be `{expected_worktree}` for this session"
                    )
                try:
                    self._session.adopt_worktree_name(new_state.worktree)
                except ValueError as error:
                    raise WorkflowStateValidationError(str(error)) from error

            logger.trace(
                f"WorkflowMonitorTask: Parsed workflow state - phase={new_state.phase}, issue={new_state.issue}"
            )

            logger.trace(f"Parsed new workflow state: phase={new_state.phase}, issue={new_state.issue}")

            # Get previous state from cache for comparison
            if self.activation is None:
                return None
            old_state = self.activation.get_cached_data("workflow_state")
            logger.trace(f"Retrieved old state from cache: {old_state is not None}")

            # Detect semantic changes
            changes = detect_workflow_changes(old_state, new_state)
            logger.trace(f"Detected {len(changes)} workflow changes")

            rendered_change = None

            # Process each detected change and get rendered content for main response
            if changes:
                rendered_change = await self._process_workflow_changes(changes)

            if not rendered_change:
                rendered_change = await render_workflow_template(self._session, "state-format")

            # Update cache with new state AFTER processing changes
            self.activation.set_cached_data("workflow_state", new_state)
            logger.trace("New workflow state cached in TaskManager")
            return rendered_change

        except WorkflowStateValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to process workflow content: {e}", exc_info=True)
            return None

    async def _process_workflow_changes(self, changes: list[ChangeEvent]) -> Optional["RenderedContent"]:
        """Process detected workflow changes and return rendered content for main response.

        Returns:
            RenderedContent with combined content and instructions, or None if no content to return
        """
        from mcp_guide.render.content import RenderedContent
        from mcp_guide.render.frontmatter_types import Frontmatter

        # Process each change using existing workflow instruction system
        rendered_list: list[RenderedContent] = []
        for change in changes:
            logger.trace(f"Processing change: {change.change_type.value}")

            # Get appropriate template pattern for this change
            template_pattern = get_instruction_template_for_change(change)

            # Render template content for main response
            rendered = await render_workflow_template(self._session, template_pattern)
            if rendered:
                rendered_list.append(rendered)
                logger.trace(
                    f"Rendered workflow content for {change.change_type.value} using pattern: {template_pattern}"
                )
            else:
                logger.trace(
                    f"Workflow content filtered or unavailable for {change.change_type.value} using pattern: {template_pattern}"
                )

        if not rendered_list:
            return None

        # Combine all rendered content and instructions
        combined_content = "\n".join(r.content for r in rendered_list)

        # Deduplicate instructions while preserving order
        seen_instructions = set()
        unique_instructions = []
        for r in rendered_list:
            if r.instruction and r.instruction not in seen_instructions:
                seen_instructions.add(r.instruction)
                unique_instructions.append(r.instruction)

        combined_instructions = "\n".join(unique_instructions)

        # Create a new RenderedContent with combined values
        # Note: Only instruction is preserved in frontmatter because:
        # - type: All workflow templates are "agent/instruction" (consistent)
        # - description: Combining descriptions doesn't make semantic sense
        # - instruction: This is the critical field that must be preserved and combined
        # frontmatter_length is 0 because this is a synthetic combined object with no source frontmatter
        first = rendered_list[0]
        return RenderedContent(
            content=combined_content,
            content_length=len(combined_content),
            frontmatter=Frontmatter(
                {"type": "agent/instruction", "instruction": combined_instructions} if combined_instructions else {}
            ),
            frontmatter_length=0,  # Synthetic combined object has no source frontmatter
            template_path=first.template_path,
            template_name=first.template_name,
        )
