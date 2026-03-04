"""Tests for workflow change detection functionality."""

import pytest

from mcp_guide.workflow.change_detection import ChangeType, detect_workflow_changes
from mcp_guide.workflow.constants import PHASE_DISCUSSION, PHASE_PLANNING
from mcp_guide.workflow.schema import WorkflowState


class TestWorkflowChangeDetection:
    """Test workflow change detection logic."""

    def test_no_changes_detected(self):
        """Test that identical states produce no changes."""
        old_state = WorkflowState(
            phase=PHASE_DISCUSSION,
            issue="test-issue",
            tracking="PROJ-123",
            description="Test description",
            queue=["item1", "item2"],
        )
        new_state = WorkflowState(
            phase=PHASE_DISCUSSION,
            issue="test-issue",
            tracking="PROJ-123",
            description="Test description",
            queue=["item1", "item2"],
        )

        changes = detect_workflow_changes(old_state, new_state)
        assert changes == []

    def test_startup_case_no_old_state(self):
        """Test that startup case (no old state) produces no changes."""
        new_state = WorkflowState(phase=PHASE_DISCUSSION, issue="test-issue")

        changes = detect_workflow_changes(None, new_state)
        assert changes == []

    def test_phase_change_detected(self):
        """Test phase change detection."""
        old_state = WorkflowState(phase=PHASE_DISCUSSION)
        new_state = WorkflowState(phase=PHASE_PLANNING)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.PHASE
        assert changes[0].from_value == PHASE_DISCUSSION
        assert changes[0].to_value == PHASE_PLANNING

    def test_issue_change_detected(self):
        """Test issue change detection."""
        old_state = WorkflowState(issue="old-issue")
        new_state = WorkflowState(issue="new-issue")

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.ISSUE
        assert changes[0].from_value == "old-issue"
        assert changes[0].to_value == "new-issue"

    def test_issue_cleared(self):
        """Test issue being cleared (set to None)."""
        old_state = WorkflowState(issue="old-issue")
        new_state = WorkflowState(issue=None)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.ISSUE
        assert changes[0].from_value == "old-issue"
        assert changes[0].to_value is None

    @pytest.mark.parametrize(
        "old_value,new_value,scenario",
        [
            ("PROJ-123", "PROJ-456", "change"),
            ("PROJ-123", None, "cleared"),
            (None, "PROJ-123", "set_from_none"),
        ],
        ids=["change", "cleared", "set_from_none"],
    )
    def test_tracking_changes(self, old_value, new_value, scenario):
        """Test tracking change detection for different scenarios."""
        old_state = WorkflowState(tracking=old_value)
        new_state = WorkflowState(tracking=new_value)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.TRACKING
        assert changes[0].from_value == old_value
        assert changes[0].to_value == new_value

    @pytest.mark.parametrize(
        "old_value,new_value,scenario",
        [
            ("Old description", "New description", "change"),
            ("Some description", None, "cleared"),
            (None, "Some description", "set_from_none"),
        ],
        ids=["change", "cleared", "set_from_none"],
    )
    def test_description_changes(self, old_value, new_value, scenario):
        """Test description change detection for different scenarios."""
        old_state = WorkflowState(description=old_value)
        new_state = WorkflowState(description=new_value)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.DESCRIPTION
        assert changes[0].from_value == old_value
        assert changes[0].to_value == new_value

    def test_queue_items_added(self):
        """Test queue item addition detection."""
        old_state = WorkflowState(queue=["item1"])
        new_state = WorkflowState(queue=["item1", "item2", "item3"])

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.QUEUE
        assert changes[0].added_items == ["item2", "item3"]  # Preserves order
        assert changes[0].removed_items is None

    def test_queue_empty_to_non_empty(self):
        """Test queue transition from empty list to non-empty list."""
        old_state = WorkflowState(queue=[])
        new_state = WorkflowState(queue=["item1"])

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.QUEUE
        assert changes[0].from_value == []
        assert changes[0].to_value == ["item1"]
        assert changes[0].added_items == ["item1"]
        assert changes[0].removed_items is None

    def test_queue_non_empty_to_empty(self):
        """Test queue transition from non-empty list to empty list."""
        old_state = WorkflowState(queue=["item1"])
        new_state = WorkflowState(queue=[])

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.QUEUE
        assert changes[0].from_value == ["item1"]
        assert changes[0].to_value == []
        assert changes[0].added_items is None
        assert changes[0].removed_items == ["item1"]

    def test_queue_items_removed(self):
        """Test queue item removal detection."""
        old_state = WorkflowState(queue=["item1", "item2", "item3"])
        new_state = WorkflowState(queue=["item1"])

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.QUEUE
        assert changes[0].added_items is None
        assert set(changes[0].removed_items) == {"item2", "item3"}

    def test_queue_items_added_and_removed(self):
        """Test queue items both added and removed."""
        old_state = WorkflowState(queue=["item1", "item2"])
        new_state = WorkflowState(queue=["item1", "item3", "item4"])

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.QUEUE
        assert changes[0].added_items == ["item3", "item4"]  # Preserves order from new list
        assert changes[0].removed_items == ["item2"]

    def test_multiple_changes_detected(self):
        """Test multiple simultaneous changes."""
        old_state = WorkflowState(
            phase=PHASE_DISCUSSION, issue="old-issue", description="Old description", queue=["item1"]
        )
        new_state = WorkflowState(
            phase=PHASE_PLANNING, issue="new-issue", description="New description", queue=["item1", "item2"]
        )

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 4
        change_types = {change.change_type for change in changes}
        assert change_types == {ChangeType.PHASE, ChangeType.ISSUE, ChangeType.DESCRIPTION, ChangeType.QUEUE}

    def test_empty_queue_changes(self):
        """Test that empty queue changes are not reported."""
        old_state = WorkflowState(queue=["item1"])
        new_state = WorkflowState(queue=["item1"])

        changes = detect_workflow_changes(old_state, new_state)

        assert changes == []
