"""Workflow context cache for template rendering."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_CONSENT, DEFAULT_WORKFLOW_FILE, DEFAULT_WORKFLOW_PHASES
from mcp_guide.workflow.flags import parse_workflow_phases

if TYPE_CHECKING:
    from mcp_guide.render.context import TemplateContext
    from mcp_guide.workflow.schema import WorkflowState


class WorkflowContextCache:
    """Cache for workflow context data used in template rendering."""

    def __init__(self, task_manager: Any) -> None:
        """Initialize with task manager reference."""
        self.task_manager = task_manager
        self._cached_context = None

    async def get_workflow_context(self) -> "TemplateContext":
        """Build workflow context from cached state."""
        from mcp_guide.render.context import TemplateContext

        # Get cached workflow state
        workflow_state: Optional["WorkflowState"] = self.task_manager.get_cached_data("workflow_state")

        if workflow_state:
            # Build workflow.transitions dict for permission metadata
            workflow_transitions = self._build_workflow_transitions()

            # Build workflow.phases dict with next phase info
            workflow_phases = self._build_workflow_phases()

            workflow_vars = {
                "workflow": {
                    "phase": workflow_state.phase,
                    "issue": workflow_state.issue,
                    "plan": workflow_state.plan,
                    "tracking": workflow_state.tracking,
                    "description": workflow_state.description,
                    "queue": workflow_state.queue,
                    "file": self.task_manager.get_cached_data("workflow_file_path") or DEFAULT_WORKFLOW_FILE,
                    "transitions": workflow_transitions,
                    "phases": workflow_phases,
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
                    "transitions": {},
                    "phases": {},
                },
            }

        # Create base context and add workflow variables as child
        base_context = TemplateContext()
        return base_context.new_child(workflow_vars)

    def _build_workflow_transitions(self) -> dict[str, Any]:
        """Build workflow.transitions dict with permission metadata for all phases."""
        logger = get_logger(__name__)

        # Get workflow configuration from feature flags
        try:
            workflow_flag = self.task_manager.get_cached_data("workflow_flag")
            if workflow_flag is None:
                workflow_config = parse_workflow_phases(DEFAULT_WORKFLOW_PHASES)
            else:
                workflow_config = parse_workflow_phases(workflow_flag)
        except Exception as e:
            logger.warning(f"Failed to parse workflow configuration: {e}")
            try:
                workflow_config = parse_workflow_phases(DEFAULT_WORKFLOW_PHASES)
            except Exception as fallback_error:
                logger.error(f"Failed to parse default workflow phases: {fallback_error}")
                return {}

        if not workflow_config.enabled:
            return {}

        # Get consent requirements
        consent_flag = self.task_manager.get_cached_data("workflow_consent_flag")
        if consent_flag is None or consent_flag is True:
            consent_config = DEFAULT_WORKFLOW_CONSENT
        elif consent_flag is False:
            consent_config = {}
        else:
            consent_config = consent_flag

        transitions: dict[str, Any] = {}
        default_phase_name = None

        # Process each configured phase
        for i, phase in enumerate(workflow_config.phases):
            # First phase is the default phase
            is_default = i == 0
            if is_default:
                default_phase_name = phase

            # Check consent requirements for this phase
            consent_value = consent_config.get(phase, [])
            # Normalize single string to list
            consent_types = [consent_value] if isinstance(consent_value, str) else consent_value

            pre_consent = "entry" in consent_types
            post_consent = "exit" in consent_types

            phase_metadata = {
                "pre": pre_consent,
                "post": post_consent,
            }

            # Only include default: true for the starting phase
            if is_default:
                phase_metadata["default"] = True

            transitions[phase] = phase_metadata

        # Add convenience field for the default phase name
        if default_phase_name:
            transitions["default"] = default_phase_name

        return transitions

    def _build_workflow_phases(self) -> dict[str, Any]:
        """Build workflow.phases dict with next phase info for templates."""
        # Get the actual configured workflow phases
        try:
            workflow_flag = self.task_manager.get_cached_data("workflow_flag")
            if workflow_flag is None:
                workflow_config = parse_workflow_phases(DEFAULT_WORKFLOW_PHASES)
            else:
                workflow_config = parse_workflow_phases(workflow_flag)
        except Exception:
            return {}

        if not workflow_config.enabled:
            return {}

        # Use phase names directly from configured phases
        configured_phases = workflow_config.phases
        phases = {}

        for i, phase in enumerate(configured_phases):
            next_phase = configured_phases[(i + 1) % len(configured_phases)]
            phases[phase] = {"next": next_phase}

        return phases

    def invalidate(self) -> None:
        """Invalidate cached workflow context."""
        self._cached_context = None
