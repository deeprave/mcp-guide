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
