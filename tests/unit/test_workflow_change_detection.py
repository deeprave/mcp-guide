"""Tests for workflow change detection functionality."""

from mcp_guide.workflow.change_detection import ChangeType, detect_workflow_changes
from mcp_guide.workflow.schema import WorkflowPhase, WorkflowState


class TestWorkflowChangeDetection:
    """Test workflow change detection logic."""

    def test_no_changes_detected(self):
        """Test that identical states produce no changes."""
        old_state = WorkflowState(
            phase=WorkflowPhase.DISCUSSION,
            issue="test-issue",
            tracking="PROJ-123",
            description="Test description",
            queue=["item1", "item2"],
        )
        new_state = WorkflowState(
            phase=WorkflowPhase.DISCUSSION,
            issue="test-issue",
            tracking="PROJ-123",
            description="Test description",
            queue=["item1", "item2"],
        )

        changes = detect_workflow_changes(old_state, new_state)
        assert changes == []

    def test_startup_case_no_old_state(self):
        """Test that startup case (no old state) produces no changes."""
        new_state = WorkflowState(phase=WorkflowPhase.DISCUSSION, issue="test-issue")

        changes = detect_workflow_changes(None, new_state)
        assert changes == []

    def test_phase_change_detected(self):
        """Test phase change detection."""
        old_state = WorkflowState(phase=WorkflowPhase.DISCUSSION)
        new_state = WorkflowState(phase=WorkflowPhase.PLANNING)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.PHASE
        assert changes[0].from_value == WorkflowPhase.DISCUSSION
        assert changes[0].to_value == WorkflowPhase.PLANNING

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

    def test_tracking_change_detected(self):
        """Test tracking change detection."""
        old_state = WorkflowState(tracking="PROJ-123")
        new_state = WorkflowState(tracking="PROJ-456")

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.TRACKING
        assert changes[0].from_value == "PROJ-123"
        assert changes[0].to_value == "PROJ-456"

    def test_tracking_cleared(self):
        """Test tracking being cleared (set to None)."""
        old_state = WorkflowState(tracking="PROJ-123")
        new_state = WorkflowState(tracking=None)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.TRACKING
        assert changes[0].from_value == "PROJ-123"
        assert changes[0].to_value is None

    def test_tracking_set_from_none(self):
        """Test tracking being set from None to a value."""
        old_state = WorkflowState(tracking=None)
        new_state = WorkflowState(tracking="PROJ-123")

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.TRACKING
        assert changes[0].from_value is None
        assert changes[0].to_value == "PROJ-123"

    def test_description_change_detected(self):
        """Test description change detection."""
        old_state = WorkflowState(description="Old description")
        new_state = WorkflowState(description="New description")

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.DESCRIPTION
        assert changes[0].from_value == "Old description"
        assert changes[0].to_value == "New description"

    def test_description_cleared(self):
        """Test description being cleared (set to None)."""
        old_state = WorkflowState(description="Some description")
        new_state = WorkflowState(description=None)

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.DESCRIPTION
        assert changes[0].from_value == "Some description"
        assert changes[0].to_value is None

    def test_description_set_from_none(self):
        """Test description being set from None to a value."""
        old_state = WorkflowState(description=None)
        new_state = WorkflowState(description="Some description")

        changes = detect_workflow_changes(old_state, new_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.DESCRIPTION
        assert changes[0].from_value is None
        assert changes[0].to_value == "Some description"

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
            phase=WorkflowPhase.DISCUSSION, issue="old-issue", description="Old description", queue=["item1"]
        )
        new_state = WorkflowState(
            phase=WorkflowPhase.PLANNING, issue="new-issue", description="New description", queue=["item1", "item2"]
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
