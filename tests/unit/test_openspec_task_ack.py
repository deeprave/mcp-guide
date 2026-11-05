"""OpenSpec acknowledgement behaviour with real rendering, queueing and persistence."""

import pytest
import yaml
from tests.helpers import create_unbound_test_session

from mcp_guide.openspec.state import parse_openspec_state
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType, TaskActivation


@pytest.mark.anyio
async def test_version_response_acknowledges_its_request_without_asset_followup(runtime, tmp_path, monkeypatch):
    """A delivered version response stops retries without a steady-state asset request."""
    docroot = tmp_path / "docs"
    templates = docroot / "_openspec"
    templates.mkdir(parents=True)
    (templates / "openspec-check.mustache").write_text("Request detection")
    (templates / "_list-format.mustache").write_text("Current changes")
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    # Acknowledgement is independent of binding/lifecycle, but remains owned by
    # an explicit activation so retirement coverage applies to queued state.
    session = create_unbound_test_session(runtime)
    manager = session.task_manager
    task = OpenSpecTask()
    task.activation = TaskActivation(manager, task, session)
    task._session = session
    now = 100.0
    monkeypatch.setattr("time.time", lambda: now)

    async def delivered():
        return (await manager.process_result(Result.ok())).additional_agent_instructions

    await task.request_detection()
    assert await delivered() == "Request detection"
    now += 31
    await manager.retry_unacknowledged()
    assert await delivered() == "Request detection"
    response = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-info.json", "content": '{"version": "1.2.3"}'},
    )
    assert response is not None and response.result
    now += 31
    await manager.retry_unacknowledged()
    assert manager.is_queue_empty()
    state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
    assert state.validated is True
    assert state.version == "1.2.3"
    assert state.checked == 131.0
