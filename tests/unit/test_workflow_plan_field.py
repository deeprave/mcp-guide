"""Test plan field in workflow schema."""

from mcp_guide.workflow.constants import PHASE_DISCUSSION, PHASE_IMPLEMENTATION, PHASE_PLANNING
from mcp_guide.workflow.schema import WorkflowState


def test_workflow_state_with_plan_field():
    """Test that WorkflowState correctly handles the plan field."""
    # Test with plan field
    state = WorkflowState(
        phase=PHASE_IMPLEMENTATION,
        issue="test-issue",
        plan=".todo/test-plan.md",
        tracking="JIRA TEST-123",
        description="Test description",
        queue=["item1", "item2"],
    )

    assert state.phase == PHASE_IMPLEMENTATION
    assert state.issue == "test-issue"
    assert state.plan == ".todo/test-plan.md"
    assert state.tracking == "JIRA TEST-123"
    assert state.description == "Test description"
    assert state.queue == ["item1", "item2"]


def test_workflow_state_without_plan_field():
    """Test that WorkflowState works without plan field (optional)."""
    state = WorkflowState(phase=PHASE_DISCUSSION, issue="test-issue")

    assert state.phase == PHASE_DISCUSSION
    assert state.issue == "test-issue"
    assert state.plan is None
    assert state.tracking is None
    assert state.description is None
    assert state.queue == []


def test_workflow_state_plan_field_ordering():
    """Test that plan field appears in correct position in model dump."""
    state = WorkflowState(
        phase=PHASE_PLANNING,
        issue="test-issue",
        plan=".todo/test-plan.md",
        tracking="JIRA TEST-123",
        description="Test description",
    )

    # Convert to dict to check field ordering
    state_dict = state.model_dump(exclude_none=True)
    keys = list(state_dict.keys())

    # Plan should come after issue and before tracking
    issue_index = keys.index("issue")
    plan_index = keys.index("plan")
    tracking_index = keys.index("tracking")

    assert plan_index == issue_index + 1
    assert tracking_index == plan_index + 1
