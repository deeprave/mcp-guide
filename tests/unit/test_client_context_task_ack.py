"""Client context collection and acknowledgement through delivered instructions."""

import json

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType


@pytest.mark.anyio
async def test_client_responses_advance_collection_and_stop_acknowledged_retries(runtime, tmp_path, monkeypatch):
    """Real context templates are retried until their corresponding client response arrives."""
    docroot = tmp_path / "docs"
    templates = docroot / "_context"
    templates.mkdir(parents=True)
    (templates / "client-context-setup.mustache").write_text("Send basic OS details")
    (templates / "client-context-detailed.mustache").write_text("Send context for {{client.os}}")
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    await runtime.feature_flags().set("allow-client-info", True)
    session = await create_bound_test_session(runtime, "context")
    manager = session.task_manager
    task = manager.get_task_by_type(ClientContextTask)
    assert task is not None
    now = 100.0
    monkeypatch.setattr("time.time", lambda: now)

    async def delivered():
        return (await manager.process_result(Result.ok())).additional_agent_instructions

    await task.handle_event(EventType.TIMER_ONCE, {})
    assert await delivered() == "Send basic OS details"
    now += 31
    await manager.retry_unacknowledged()
    assert await delivered() == "Send basic OS details"
    os_info = {"client": {"os": "linux"}}
    await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".client-os.json", "content": json.dumps(os_info)})
    assert manager.get_cached_data("client_os_info") == os_info
    assert await delivered() == "Send context for linux"
    now += 31
    await manager.retry_unacknowledged()
    assert await delivered() == "Send context for linux"
    assert manager.is_queue_empty()  # Basic OS instruction has been acknowledged.
    details = {"editor": {"name": "test-editor"}}
    await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".client-context.json", "content": json.dumps(details)})
    assert manager.get_cached_data("client_context_info") == details
    now += 31
    await manager.retry_unacknowledged()
    assert manager.is_queue_empty()
