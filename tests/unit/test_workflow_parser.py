from mcp_guide.workflow.parser import parse_workflow_state


def test_parse_workflow_state_accepts_null_queue() -> None:
    content = """phase: check
issue: fix-no-project-instruction
queue:
"""

    state = parse_workflow_state(content)

    assert state is not None
    assert state.phase == "check"
    assert state.issue == "fix-no-project-instruction"
    assert state.queue == []
    assert state.plan is None


def test_parse_workflow_state_preserves_plan_and_tracking() -> None:
    state = parse_workflow_state(
        "Phase: IMPLEMENTATION\nIssue: test-issue\nPlan: .todo/plan.md\n"
        "Tracking: JIRA TEST-123\nDescription: Work in progress\nQueue: [next, later]\n"
    )
    assert state is not None
    assert state.phase == "implementation"
    assert state.issue == "test-issue"
    assert state.plan == ".todo/plan.md"
    assert state.tracking == "JIRA TEST-123"
    assert state.description == "Work in progress"
    assert state.queue == ["next", "later"]
