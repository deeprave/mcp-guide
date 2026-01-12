"""Workflow context cache with separate lifecycle from project context."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_core.mcp_log import get_logger
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_FILE

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager
    from mcp_guide.utils.template_context import TemplateContext
    from mcp_guide.workflow.schema import WorkflowPhase, WorkflowState

logger = get_logger(__name__)


class WorkflowContextCache:
    """Manages workflow-specific template context with independent lifecycle."""

    def __init__(self, task_manager: "TaskManager"):
        self.task_manager = task_manager
        self._cached_context: Optional["TemplateContext"] = None
        self._last_state_mtime: Optional[float] = None

    async def get_workflow_context(self) -> "TemplateContext":
        """Get workflow context, rebuilding if state has changed."""

        # Check if we need to rebuild context
        current_mtime = self.task_manager.get_cached_data("workflow_state_mtime")

        if self._cached_context is None or current_mtime != self._last_state_mtime:
            self._cached_context = await self._build_workflow_context()
            self._last_state_mtime = current_mtime

        return self._cached_context

    async def _build_workflow_context(self) -> "TemplateContext":
        """Build workflow context from cached state."""
        from mcp_guide.utils.template_context import TemplateContext

        # Get cached workflow state
        workflow_state: Optional["WorkflowState"] = self.task_manager.get_cached_data("workflow_state")

        if workflow_state:
            # Build workflow_state dict for phase availability and consent rules
            workflow_state_dict = self._build_workflow_state_dict(workflow_state)

            # Build workflow.transitions dict for permission metadata
            workflow_transitions = self._build_workflow_transitions()

            workflow_vars = {
                "workflow": {
                    "phase": workflow_state.phase,
                    "issue": workflow_state.issue,
                    "plan": workflow_state.plan,
                    "tracking": workflow_state.tracking,
                    "description": workflow_state.description,
                    "queue": workflow_state.queue,
                    "file": self.task_manager.get_cached_data("workflow_file_path") or DEFAULT_WORKFLOW_FILE,
                    "phase_list": list(workflow_state_dict.keys()),
                    "phases": workflow_state_dict,
                    "transitions": workflow_transitions,
                },
            }
        else:
            # Default empty workflow context
            workflow_vars = {
                "workflow": {
                    "phase": None,
                    "issue": None,
                    "plan": None,
                    "tracking": None,
                    "description": None,
                    "queue": [],
                    "file": DEFAULT_WORKFLOW_FILE,
                    "phase_list": [],
                    "phases": {},
                    "transitions": {},
                },
            }

        # Create base context and add workflow variables as child
        base_context = TemplateContext()
        return base_context.new_child(workflow_vars)

    def _build_workflow_state_dict(self, workflow_state: "WorkflowState") -> dict[str, Any]:
        """Build workflow_state dict with phase availability and consent rules."""
        from mcp_guide.workflow.schema import WorkflowPhase

        # Parse workflow flag to determine available phases
        # Format: "discussion planning *implementation* check review"
        # Asterisks indicate consent requirements

        workflow_flag = getattr(workflow_state, "workflow", None)
        if workflow_flag in (None, False):
            # No workflow configured or disabled
            return {}
        elif workflow_flag is True:
            # workflow = True enables default phases with consent markers
            from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_PHASES

            workflow_flag = " ".join(DEFAULT_WORKFLOW_PHASES)
        # Otherwise workflow_flag should be a string with phase names

        # Ensure workflow_flag is a valid string before processing
        if not isinstance(workflow_flag, str):
            return {}

        phases = workflow_flag.split()

        state_dict: dict[str, Any | bool | str | None] = {}

        for phase in WorkflowPhase:
            phase_name = phase.value

            # Check if phase is in workflow flag
            phase_entry = None
            for flag_phase in phases:
                clean_phase = flag_phase.strip("*")
                if clean_phase == phase_name:
                    phase_entry = flag_phase
                    break

            if phase_entry:
                # Determine consent requirements
                pre_consent = phase_entry.startswith("*")
                post_consent = phase_entry.endswith("*") and not phase_entry.startswith("*")
                if phase_entry.startswith("*") and phase_entry.endswith("*"):
                    post_consent = True

                # Find next phase using match statement
                next_phase = self._get_next_phase(phase, phases)

                state_dict[phase_name] = {"pre_consent": pre_consent, "post_consent": post_consent, "next": next_phase}
            else:
                state_dict[phase_name] = None

        return state_dict

    def _get_next_phase(self, current_phase: "WorkflowPhase", available_phases: list[str]) -> Optional[str]:
        """Get next available phase using match statement."""
        from mcp_guide.workflow.schema import WorkflowPhase

        # Get clean phase names from available phases
        clean_phases = {p.strip("*") for p in available_phases}

        match current_phase:
            case WorkflowPhase.DISCUSSION:
                if WorkflowPhase.PLANNING.value in clean_phases:
                    return WorkflowPhase.PLANNING.value
                elif WorkflowPhase.IMPLEMENTATION.value in clean_phases:
                    return WorkflowPhase.IMPLEMENTATION.value
                elif WorkflowPhase.CHECK.value in clean_phases:
                    return WorkflowPhase.CHECK.value
                elif WorkflowPhase.REVIEW.value in clean_phases:
                    return WorkflowPhase.REVIEW.value
            case WorkflowPhase.PLANNING:
                if WorkflowPhase.IMPLEMENTATION.value in clean_phases:
                    return WorkflowPhase.IMPLEMENTATION.value
                elif WorkflowPhase.CHECK.value in clean_phases:
                    return WorkflowPhase.CHECK.value
                elif WorkflowPhase.REVIEW.value in clean_phases:
                    return WorkflowPhase.REVIEW.value
            case WorkflowPhase.IMPLEMENTATION:
                if WorkflowPhase.CHECK.value in clean_phases:
                    return WorkflowPhase.CHECK.value
                elif WorkflowPhase.REVIEW.value in clean_phases:
                    return WorkflowPhase.REVIEW.value
            case WorkflowPhase.CHECK:
                if WorkflowPhase.REVIEW.value in clean_phases:
                    return WorkflowPhase.REVIEW.value
            case WorkflowPhase.REVIEW:
                return None
            case _:
                raise ValueError(f"Unknown workflow phase: {current_phase}")

        return None

    def _build_workflow_transitions(self) -> dict[str, Any]:
        """Build workflow.transitions dict with permission metadata for all phases.

        Returns:
            Dictionary mapping phase names to permission metadata
        """
        from mcp_core.mcp_log import get_logger
        from mcp_guide.workflow.flags import extract_phase_name, parse_workflow_phases

        logger = get_logger(__name__)

        # Get workflow configuration from feature flags
        try:
            # Get workflow flag from task manager cache or use default
            workflow_flag = self.task_manager.get_cached_data("workflow_flag")
            if workflow_flag is None:
                # Use default workflow phases
                from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_PHASES

                workflow_config = parse_workflow_phases(DEFAULT_WORKFLOW_PHASES)
            else:
                workflow_config = parse_workflow_phases(workflow_flag)
        except Exception as e:
            # Fallback to default if parsing fails
            logger.warning(f"Failed to parse workflow configuration: {e}")
            from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_PHASES

            try:
                workflow_config = parse_workflow_phases(DEFAULT_WORKFLOW_PHASES)
            except Exception as fallback_error:
                logger.error(f"Failed to parse default workflow phases: {fallback_error}")
                return {}

        if not workflow_config.enabled:
            return {}

        transitions: dict[str, Any] = {}
        default_phase_name = None

        # Process each configured phase
        for i, phase_with_markers in enumerate(workflow_config.phases):
            clean_phase = extract_phase_name(phase_with_markers)

            # First phase is the default phase
            is_default = i == 0
            if is_default:
                default_phase_name = clean_phase

            # Determine permission requirements from markers
            pre_consent = phase_with_markers.startswith("*")
            post_consent = phase_with_markers.endswith("*")

            # Handle case where phase has both markers (*phase*)
            if phase_with_markers.startswith("*") and phase_with_markers.endswith("*") and len(phase_with_markers) > 2:
                pre_consent = True
                post_consent = True

            phase_metadata = {
                "pre": pre_consent,
                "post": post_consent,
            }

            # Only include default: true for the starting phase
            if is_default:
                phase_metadata["default"] = True

            transitions[clean_phase] = phase_metadata

        # Add convenience field for the default phase name
        if default_phase_name:
            transitions["default"] = default_phase_name

        return transitions

    def invalidate(self) -> None:
        """Invalidate cached workflow context."""
        self._cached_context = None
        self._last_state_mtime = None
        # Clear any related cached data in TaskManager
        self.task_manager.clear_cached_data("workflow_context_cache")
        logger.debug("Workflow context cache invalidated")
