"""Client file replies update the real workflow task and its cached state."""

import pytest
import yaml

from mcp_guide.tools.tool_filesystem import SendFileContentArgs, internal_send_file_content
from mcp_guide.workflow.tasks import WorkflowMonitorTask
from tests.helpers import create_bound_test_session, request_context_for


@pytest.mark.anyio
async def test_workflow_file_reply_updates_the_bound_sessions_state(runtime, tmp_path):
    templates = tmp_path / "docs" / "_workflow"
    templates.mkdir(parents=True)
    (templates / "state-format.mustache").write_text("Workflow received")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(templates.parent), "projects": {}, "feature_flags": {"workflow": True}})
    )
    session = await create_bound_test_session(runtime, "workflow")
    assert session.task_manager.get_task_by_type(WorkflowMonitorTask) is not None
    state = {"phase": "review", "issue": "pytest-maintenance", "description": "Review tests", "queue": ["next-issue"]}
    response = await internal_send_file_content(
        SendFileContentArgs(path=".guide.yaml", content=yaml.safe_dump(state), mtime=1234567890.0),
        await request_context_for(session),
    )
    assert response.success, response.error
    assert response.value == "Workflow received"
    cached = session.task_manager.get_cached_data("workflow_state")
    assert cached.phase == state["phase"]
    assert cached.issue == state["issue"]
    assert cached.description == state["description"]
    assert cached.queue == state["queue"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("content", "error"),
    [
        ("phase: [", "Invalid workflow file: YAML syntax is invalid"),
        ("- phase: implementation\n", "Invalid workflow file: expected a YAML mapping"),
        ("issue: sample\n", "Invalid workflow file: missing required `phase` field"),
        (
            "phase: implementation\nissue: sample\ntracking:\n  openspec: sample\n",
            "Invalid workflow file: `tracking` must be a string",
        ),
        ("phase: implementation\nqueue: sample\n", "Invalid workflow file: one or more fields have invalid values"),
    ],
    ids=["invalid-yaml", "non-mapping", "missing-phase", "structured-tracking", "invalid-field-type"],
)
async def test_workflow_file_reply_rejects_invalid_content_without_replacing_cached_state(
    runtime, tmp_path, content, error
):
    templates = tmp_path / "docs" / "_workflow"
    templates.mkdir(parents=True)
    (templates / "state-format.mustache").write_text("Workflow received")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(templates.parent), "projects": {}, "feature_flags": {"workflow": True}})
    )
    session = await create_bound_test_session(runtime, "workflow")

    valid = await internal_send_file_content(
        SendFileContentArgs(path=".guide.yaml", content="phase: implementation\nissue: sample\n"),
        await request_context_for(session),
    )
    assert valid.success, valid.error

    response = await internal_send_file_content(
        SendFileContentArgs(path=".guide.yaml", content=content),
        await request_context_for(session),
    )

    assert not response.success
    assert response.error == error
    cached = session.task_manager.get_cached_data("workflow_state")
    assert (cached.phase, cached.issue) == ("implementation", "sample")
