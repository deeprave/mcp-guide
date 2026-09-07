"""Semantic workflow changes preserve values and queue ordering."""

import pytest

from mcp_guide.workflow.change_detection import ChangeEvent, ChangeType, detect_workflow_changes
from mcp_guide.workflow.schema import WorkflowState


@pytest.mark.parametrize("initial", [True, False], ids=["startup", "unchanged"])
def test_no_changes(initial):
    state = WorkflowState(
        phase="discussion", issue="test", tracking="PROJ-123", description="Description", queue=["item1", "item2"]
    )
    assert detect_workflow_changes(None if initial else state.model_copy(deep=True), state) == []


@pytest.mark.parametrize(
    "field,old,new,kind",
    [
        ("phase", "discussion", "planning", ChangeType.PHASE),
        ("issue", "old-issue", "new-issue", ChangeType.ISSUE),
        ("issue", "old-issue", None, ChangeType.ISSUE),
        ("tracking", "PROJ-123", "PROJ-456", ChangeType.TRACKING),
        ("tracking", "PROJ-123", None, ChangeType.TRACKING),
        ("tracking", None, "PROJ-123", ChangeType.TRACKING),
        ("description", "Old", "New", ChangeType.DESCRIPTION),
        ("description", "Old", None, ChangeType.DESCRIPTION),
        ("description", None, "New", ChangeType.DESCRIPTION),
    ],
)
def test_scalar_change(field, old, new, kind):
    assert detect_workflow_changes(WorkflowState(**{field: old}), WorkflowState(**{field: new})) == [
        ChangeEvent(kind, old, new)
    ]


@pytest.mark.parametrize(
    "old,new,added,removed",
    [
        (["item1"], ["item1", "item3", "item2"], ["item3", "item2"], None),
        ([], ["item1"], ["item1"], None),
        (["item1"], [], None, ["item1"]),
        (["item1", "item3", "item2"], ["item1"], None, ["item3", "item2"]),
        (["item1", "item2"], ["item1", "item3", "item4"], ["item3", "item4"], ["item2"]),
    ],
)
def test_queue_changes_preserve_source_order(old, new, added, removed):
    assert detect_workflow_changes(WorkflowState(queue=old), WorkflowState(queue=new)) == [
        ChangeEvent(ChangeType.QUEUE, old, new, added, removed)
    ]


def test_multiple_changes_retain_all_values_in_event_order():
    old = WorkflowState(phase="discussion", issue="old", tracking="PROJ-123", description="Old", queue=["item1"])
    new = WorkflowState(phase="planning", issue="new", tracking="PROJ-456", description="New", queue=["item1", "item2"])
    assert detect_workflow_changes(old, new) == [
        ChangeEvent(ChangeType.PHASE, "discussion", "planning"),
        ChangeEvent(ChangeType.ISSUE, "old", "new"),
        ChangeEvent(ChangeType.TRACKING, "PROJ-123", "PROJ-456"),
        ChangeEvent(ChangeType.DESCRIPTION, "Old", "New"),
        ChangeEvent(ChangeType.QUEUE, ["item1"], ["item1", "item2"], ["item2"], None),
    ]
