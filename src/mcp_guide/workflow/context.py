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
            # Build workflow.phases dict with next phase info and consent
            workflow_phases, workflow_next, workflow_consent = self._build_workflow_phases()

            workflow_vars = {
                "workflow": {
                    "phase": workflow_state.phase,
                    "issue": workflow_state.issue,
                    "plan": workflow_state.plan,
                    "tracking": workflow_state.tracking,
                    "description": workflow_state.description,
                    "queue": workflow_state.queue,
                    "file": self.task_manager.get_cached_data("workflow_file_path") or DEFAULT_WORKFLOW_FILE,
                    "phases": workflow_phases,
                    "next": workflow_next,
                    "consent": workflow_consent,
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
                    "phases": {},
                    "next": {},
                    "consent": {},
                },
            }

        # Create base context and add workflow variables as child
        base_context = TemplateContext()
        return base_context.new_child(workflow_vars)

    def _build_workflow_phases(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Build workflow.phases, workflow.next, and workflow.consent dicts.

        Returns:
            Tuple of (phases, next, consent) dicts for template context.
        """
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
                return {}, {}, {}

        if not workflow_config.enabled:
            return {}, {}, {}

        # Get consent requirements
        consent_flag = self.task_manager.get_cached_data("workflow_consent_flag")
        if consent_flag is None or consent_flag is True:
            consent_config = DEFAULT_WORKFLOW_CONSENT
        elif consent_flag is False:
            consent_config = {}
        else:
            consent_config = consent_flag

        # Helper to normalize consent config values
        def _get_consent_types(phase_name: str) -> list[str]:
            """Normalize consent config value to list of consent types."""
            consent_value = consent_config.get(phase_name, [])
            return [consent_value] if isinstance(consent_value, str) else consent_value

        # Get current phase
        workflow_state: Optional["WorkflowState"] = self.task_manager.get_cached_data("workflow_state")
        current_phase = workflow_state.phase if workflow_state else None

        # Build phases dict with next phase info
        configured_phases = workflow_config.phases
        phases = {}
        next_phase_name = None
        current_phase_index = -1

        for i, phase in enumerate(configured_phases):
            next_phase = configured_phases[(i + 1) % len(configured_phases)]
            phases[phase] = {"next": next_phase}

            if phase == current_phase:
                current_phase_index = i
                next_phase_name = next_phase

        # Build workflow.next object
        workflow_next: dict[str, Any] = {}
        next_consent_types: list[str] = []
        if next_phase_name:
            workflow_next["value"] = next_phase_name

            # Check if next phase has entry consent
            next_consent_types = _get_consent_types(next_phase_name)

            next_consent: dict[str, bool] = {}
            if "entry" in next_consent_types:
                next_consent["entry"] = True
            if "exit" in next_consent_types:
                next_consent["exit"] = True

            # Only add consent dict if there are consent requirements
            if next_consent:
                workflow_next["consent"] = next_consent

        # Build workflow.consent for current phase
        workflow_consent: dict[str, Any] = {}
        if current_phase:
            current_consent_types = _get_consent_types(current_phase)

            # Check current phase consent
            if "entry" in current_consent_types:
                workflow_consent["entry"] = True

            # Check exit consent - set to true if current phase has exit OR next phase has entry
            current_exit = "exit" in current_consent_types
            next_entry = "entry" in next_consent_types if next_phase_name else False

            if current_exit or next_entry:
                workflow_consent["exit"] = True

            # Add phase-specific consent flags for all phases
            for phase in configured_phases:
                phase_consent_types = _get_consent_types(phase)

                if "entry" in phase_consent_types or "exit" in phase_consent_types:
                    workflow_consent[phase] = True

        return phases, workflow_next, workflow_consent

    def invalidate(self) -> None:
        """Invalidate cached workflow context."""
        self._cached_context = None
