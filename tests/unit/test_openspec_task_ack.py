"""OpenSpec acknowledgement behaviour with real rendering, queueing and persistence."""

import pytest
import yaml
from tests.helpers import create_unbound_test_session

from mcp_guide.openspec.state import parse_openspec_state
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType


@pytest.mark.anyio
@pytest.mark.parametrize(
    "check_kind,event,data,followup",
    [
        ("cli", EventType.FS_COMMAND, {"command": "openspec", "found": True, "path": "/usr/bin/openspec"}, "version"),
        ("version", EventType.FS_FILE_CONTENT, {"path": ".openspec-version.txt", "content": "1.2.3"}, "project"),
        ("project", EventType.FS_DIRECTORY, {"path": "openspec", "files": [{"name": "config.yaml"}]}, "changes"),
        ("changes", EventType.FS_FILE_CONTENT, {"path": ".openspec-changes.json", "content": '{"changes": []}'}, None),
    ],
    ids=["cli", "version", "project", "changes"],
)
async def test_responses_acknowledge_requests_and_only_followup_is_retried(
    runtime, tmp_path, monkeypatch, check_kind, event, data, followup
):
    """A delivered response stops its request's retries and advances the OpenSpec check."""
    docroot = tmp_path / "docs"
    templates = docroot / "_openspec"
    templates.mkdir(parents=True)
    for name, pattern in {
        "cli": "openspec-cli-check",
        "version": "openspec-version-check",
        "project": "openspec-project-check",
        "changes": "openspec-get-changes",
    }.items():
        (templates / f"{pattern}.mustache").write_text(f"Request {name}")
    (templates / "_list-format.mustache").write_text("Current changes")
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    # Acknowledgement is independent of binding/activation, which has lifecycle coverage.
    session = create_unbound_test_session(runtime)
    manager = session.task_manager
    task = OpenSpecTask(manager)
    now = 100.0
    monkeypatch.setattr("time.time", lambda: now)

    async def delivered():
        return (await manager.process_result(Result.ok())).additional_agent_instructions

    methods = {
        "cli": task.request_cli_check,
        "version": task.request_version_check,
        "project": task.request_project_check,
        "changes": task.request_changes_json,
    }
    await methods[check_kind]()
    assert await delivered() == f"Request {check_kind}"
    now += 31
    await manager.retry_unacknowledged()
    assert await delivered() == f"Request {check_kind}"
    response = await task.handle_event(event, data)
    assert response is not None and response.result
    if followup:
        assert await delivered() == f"Request {followup}"
    else:
        assert response.rendered_content.content == "Current changes"
        assert manager.get_cached_data("openspec_changes") == []
    now += 31
    await manager.retry_unacknowledged()
    if followup:
        assert await delivered() == f"Request {followup}"
    assert manager.is_queue_empty()
    if check_kind == "version":
        state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
        assert state.validated is True
        assert state.version == "1.2.3"
        assert state.checked == 131.0
