"""Instruction generation for workflow change events."""

from mcp_core.mcp_log import get_logger
from mcp_guide.workflow.change_detection import ChangeEvent, ChangeType

logger = get_logger(__name__)


def get_instruction_template_for_change(change: ChangeEvent) -> str:
    """Get the appropriate template pattern for a workflow change event.

    Args:
        change: The detected change event

    Returns:
        Template pattern string for existing workflow instruction system
    """
    if change.change_type == ChangeType.PHASE and change.to_value is not None:
        # For phase changes, use phase-specific template
        return f"*{change.to_value}"
    else:
        # For other changes, use monitoring-result template
        return "monitoring-result"
