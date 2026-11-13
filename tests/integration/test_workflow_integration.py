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


@pytest.mark.anyio
async def test_linked_worktree_adopts_its_existing_workflow_label_then_rejects_a_change(runtime, tmp_path):
    templates = tmp_path / "docs" / "_workflow"
    templates.mkdir(parents=True)
    (templates / "state-format.mustache").write_text("Workflow received")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(templates.parent), "projects": {}, "feature_flags": {"workflow": True}})
    )
    from mcp_guide.session import bind_session_project
    from tests.helpers import create_unbound_test_session

    session = create_unbound_test_session(runtime)
    await bind_session_project(session, "/client/project", worktree="/client/project_languid-lizard")
    response = await internal_send_file_content(
        SendFileContentArgs(
            path=".guide.yaml",
            content="phase: implementation\nworktree: another-worktree\n",
        ),
        await request_context_for(session),
    )

    assert response.success, response.error
    assert session.worktree_name == "another-worktree"

    changed = await internal_send_file_content(
        SendFileContentArgs(path=".guide.yaml", content="phase: implementation\nworktree: changed-worktree\n"),
        await request_context_for(session),
    )

    assert not changed.success
    assert changed.error == "Invalid workflow file: worktree must be `another-worktree` for this session"


@pytest.mark.anyio
async def test_linked_worktree_rejects_root_as_a_local_workflow_label(runtime, tmp_path):
    templates = tmp_path / "docs" / "_workflow"
    templates.mkdir(parents=True)
    (templates / "state-format.mustache").write_text("Workflow received")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(templates.parent), "projects": {}, "feature_flags": {"workflow": True}})
    )
    from mcp_guide.session import bind_session_project
    from tests.helpers import create_unbound_test_session

    session = create_unbound_test_session(runtime)
    await bind_session_project(session, "/client/project", worktree="/client/any-directory-name")
    response = await internal_send_file_content(
        SendFileContentArgs(path=".guide.yaml", content="phase: implementation\nworktree: root\n"),
        await request_context_for(session),
    )

    assert not response.success
    assert response.error == "Only the primary checkout may use the `root` worktree label"


@pytest.mark.anyio
async def test_linked_worktree_processes_its_initial_workflow_file_when_workflow_is_disabled(runtime, tmp_path):
    templates = tmp_path / "docs" / "_workflow"
    templates.mkdir(parents=True)
    (templates / "state-format.mustache").write_text("Workflow received")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(templates.parent), "projects": {}, "feature_flags": {"workflow": False}})
    )
    from mcp_guide.session import bind_session_project
    from tests.helpers import create_unbound_test_session

    session = create_unbound_test_session(runtime)
    await bind_session_project(session, "/client/project", worktree="/client/linked-checkout")

    from mcp_guide.feature_flags.types import to_raw_feature_value
    from mcp_guide.models import resolve_all_flags

    assert to_raw_feature_value((await resolve_all_flags(session))["workflow"]) == ["discussion", "implementation"]

    response = await internal_send_file_content(
        SendFileContentArgs(path=".guide.yaml", content="phase: discussion\nworktree: calm-otter\n"),
        await request_context_for(session),
    )

    assert response.success, response.error
    assert session.worktree_name == "calm-otter"
