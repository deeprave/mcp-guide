"""Change detection types and data structures for workflow monitoring."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from mcp_guide.workflow.schema import WorkflowState


class ChangeType(Enum):
    """Types of workflow state changes that can be detected."""

    PHASE = "phase"
    ISSUE = "issue"
    TRACKING = "tracking"
    DESCRIPTION = "description"
    QUEUE = "queue"


@dataclass
class ChangeEvent:
    """Represents a detected change in workflow state."""

    change_type: ChangeType
    from_value: Optional[Any] = None
    to_value: Optional[Any] = None
    added_items: Optional[list[str]] = None  # For queue additions
    removed_items: Optional[list[str]] = None  # For queue removals


def detect_workflow_changes(old_state: Optional[WorkflowState], new_state: WorkflowState) -> list[ChangeEvent]:
    """Detect semantic changes between old and new workflow states.

    Args:
        old_state: Previous workflow state (None on startup)
        new_state: New workflow state

    Returns:
        List of detected changes
    """
    changes: list[ChangeEvent] = []

    # Handle startup case (no previous state)
    if old_state is None:
        return changes

    # Check phase change
    if old_state.phase != new_state.phase:
        changes.append(ChangeEvent(change_type=ChangeType.PHASE, from_value=old_state.phase, to_value=new_state.phase))

    # Check issue change
    if old_state.issue != new_state.issue:
        changes.append(ChangeEvent(change_type=ChangeType.ISSUE, from_value=old_state.issue, to_value=new_state.issue))

    # Check tracking change
    if old_state.tracking != new_state.tracking:
        changes.append(
            ChangeEvent(change_type=ChangeType.TRACKING, from_value=old_state.tracking, to_value=new_state.tracking)
        )

    # Check description change
    if old_state.description != new_state.description:
        changes.append(
            ChangeEvent(
                change_type=ChangeType.DESCRIPTION, from_value=old_state.description, to_value=new_state.description
            )
        )

    # Check queue changes
    old_queue = set(old_state.queue)
    new_queue = set(new_state.queue)

    added_items = sorted(new_queue - old_queue)
    removed_items = sorted(old_queue - new_queue)

    if added_items or removed_items:
        changes.append(
            ChangeEvent(
                change_type=ChangeType.QUEUE,
                from_value=old_state.queue,
                to_value=new_state.queue,
                added_items=added_items if added_items else None,
                removed_items=removed_items if removed_items else None,
            )
        )

    return changes
