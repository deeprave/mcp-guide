"""Startup document-update prompts use real flags, version files and rendering."""

import pytest
import yaml
from tests.helpers import bind_isolated_test_session, create_unbound_test_session

from mcp_guide import __version__
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType
from mcp_guide.tasks.update_task import McpUpdateTask


@pytest.mark.anyio
@pytest.mark.parametrize(
    "flag,version,exists,prompt",
    [
        (None, "0.0.1", True, True),
        (True, "0.0.1", True, True),
        (False, "0.0.1", True, False),
        (True, __version__, True, False),
        (True, None, True, False),
        (True, None, False, False),
    ],
    ids=["opt-out-default", "enabled-old", "disabled-old", "current-version", "missing-version", "missing-root"],
)
async def test_startup_prompt_and_acknowledgement(runtime, tmp_path, flag, version, exists, prompt):
    docroot = tmp_path / "documents"
    if exists:
        (docroot / "_system").mkdir(parents=True)
        (docroot / "_system" / "_update.mustache").write_text("Update documents now")
        if version is not None:
            (docroot / ".version").write_text(version)
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump(
            {"docroot": str(docroot), "projects": {}, "feature_flags": {} if flag is None else {"autoupdate": flag}}
        )
    )
    session = await bind_isolated_test_session(runtime)
    manager = session.task_manager
    task = manager.get_task_by_type(McpUpdateTask)
    assert task is not None
    assert await task.handle_event(EventType.FS_DIRECTORY, {}) is None
    result = await task.handle_event(EventType.TIMER_ONCE, {})
    assert result.result
    assert manager.get_task_by_type(McpUpdateTask) is None
    assert manager.is_queue_empty() is not prompt
    if prompt:
        delivered = await manager.process_result(Result.ok())
        assert delivered.additional_agent_instructions == "Update documents now"
        # Acknowledging also removes an already queued retry, not just a private ID.
        await manager.queue_instruction("Update documents now")
        await task.acknowledge_update()
        await task.acknowledge_update()
        assert manager.is_queue_empty()
    else:
        assert (await manager.process_result(Result.ok())).additional_agent_instructions is None


@pytest.mark.anyio
@pytest.mark.parametrize("missing", [False, True], ids=["unsafe-docroot", "missing-package"])
async def test_unavailable_template_source_prevents_prompt(runtime, tmp_path, monkeypatch, missing):
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    (tmp_path / ".version").write_text("0.0.1")

    # Control package location, leaving actual docroot validation in place.
    async def package_templates():
        if missing:
            raise FileNotFoundError("Templates directory not found")
        return tmp_path

    monkeypatch.setattr("mcp_guide.installer.core.get_templates_path", package_templates)
    session = create_unbound_test_session(runtime)
    task = session.task_manager.get_task_by_type(McpUpdateTask)
    assert task is not None
    result = await task.handle_event(EventType.TIMER_ONCE, {})
    assert result.result
    assert session.task_manager.is_queue_empty()
    assert session.task_manager.get_task_by_type(McpUpdateTask) is None
