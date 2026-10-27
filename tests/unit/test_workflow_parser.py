import pytest

from mcp_guide.workflow.parser import WorkflowStateValidationError, parse_workflow_state


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


@pytest.mark.parametrize(
    ("content", "error"),
    [
        ("phase: [", "YAML syntax is invalid"),
        ("- phase: implementation\n", "expected a YAML mapping"),
        ("issue: sample\n", "missing required `phase` field"),
        ("phase: implementation\ntracking:\n  openspec: sample\n", "`tracking` must be a string"),
        ("phase: implementation\nqueue: sample\n", "one or more fields have invalid values"),
        ("phase: unsupported\n", "unsupported phase `unsupported`"),
    ],
    ids=["invalid-yaml", "non-mapping", "missing-phase", "structured-tracking", "invalid-field-type", "unknown-phase"],
)
def test_parse_workflow_state_reports_validation_errors_when_requested(content: str, error: str) -> None:
    with pytest.raises(WorkflowStateValidationError, match=error):
        parse_workflow_state(content, raise_validation_error=True)


def test_parse_workflow_state_reports_unexpected_errors_when_requested(monkeypatch) -> None:
    """Strict parsing must not silently acknowledge an unexpected parser error."""

    def raise_unexpected_error(_content: str):
        raise RuntimeError("unexpected")

    monkeypatch.setattr("mcp_guide.workflow.parser.yaml.safe_load", raise_unexpected_error)

    with pytest.raises(WorkflowStateValidationError, match="unable to process content"):
        parse_workflow_state("phase: discussion\n", raise_validation_error=True)
