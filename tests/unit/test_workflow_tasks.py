"""Workflow task behaviour through real rendering, state and instructions."""

from datetime import datetime
from pathlib import Path

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.template import render_template
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.manager import aggregate_event_results
from mcp_guide.workflow.tasks import WorkflowMonitorTask


@pytest.fixture
async def workflow_task(runtime, tmp_path):
    docroot = tmp_path / "docs"
    templates = docroot / "_workflow"
    templates.mkdir(parents=True)
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    session = await create_bound_test_session(runtime, "workflow")
    manager = session.task_manager
    assert manager.get_task_by_type(WorkflowMonitorTask) is None
    await session.project_flags().set("workflow", True)
    task = manager.get_task_by_type(WorkflowMonitorTask)
    assert task is not None
    try:
        yield session, manager, task, templates
    finally:
        await manager.cleanup()


@pytest.mark.anyio
async def test_initialisation_and_file_events_deliver_guidance_and_update_state(workflow_task, monkeypatch):
    session, manager, task, templates = workflow_task
    (templates / "monitoring-setup.mustache").write_text("Send workflow state")
    (templates / "monitoring-reminder.mustache").write_text("Refresh workflow state")
    (templates / "state-format.mustache").write_text(
        "---\ninstruction: Follow the workflow format\n---\n# Workflow format"
    )

    now = 100.0
    monkeypatch.setattr("mcp_guide.task_manager.manager.time.time", lambda: now)
    initialised = await task.handle_event(EventType.TIMER_ONCE, {})
    assert initialised.result is True
    assert (await manager.process_result(Result.ok())).additional_agent_instructions == "Send workflow state"
    await task.handle_event(EventType.TIMER_ONCE, {})
    assert manager.is_queue_empty()

    for event, payload in [
        (EventType.FS_FILE_CONTENT, {"path": "unrelated.yaml", "content": "phase: other"}),
        (EventType.FS_DIRECTORY, {"path": ".guide", "action": "modified"}),
    ]:
        assert await task.handle_event(event, payload) is None
        assert manager.get_cached_data("workflow_state") is None
        assert manager.is_queue_empty()

    await task.handle_event(EventType.TIMER, {"timer_interval": 600.0})
    assert not manager.is_queue_empty()
    content = "phase: discussion\nissue: example\n"
    for _ in range(2):
        event = await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": content})
        response = aggregate_event_results([event])
        assert response.value == "# Workflow format"
        assert response.instruction == "Follow the workflow format"
        assert response.disposition == "agent/instruction"
        state = manager.get_cached_data("workflow_state")
        assert (state.phase, state.issue) == ("discussion", "example")
        assert manager.get_cached_data("workflow_change_content") is None

    # Receiving state acknowledges both setup and reminder: neither may retry.
    assert manager.is_queue_empty()
    now += 31
    await manager.retry_unacknowledged()
    assert manager.is_queue_empty()
    await session.project_flags().set("workflow", False)
    assert manager.get_task_by_type(WorkflowMonitorTask) is None


@pytest.mark.anyio
@pytest.mark.parametrize("semantic_available", [True, False], ids=["semantic-response", "filtered-fallback"])
async def test_semantic_changes_use_matching_template_or_filtered_fallback(workflow_task, semantic_available):
    _, manager, task, templates = workflow_task
    from mcp_guide.workflow.parser import parse_workflow_state

    manager.set_cached_data("workflow_state", parse_workflow_state("phase: discussion\n"))
    (templates / "state-format.mustache").write_text("---\nrequires-never-enabled: true\n---\nFiltered format")
    prefix = "" if semantic_available else "---\nrequires-never-enabled: true\n---\n"
    (templates / "planning.mustache").write_text(prefix + "# Planning")
    event = await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "phase: planning\n"})
    assert event.result is True
    if semantic_available:
        assert aggregate_event_results([event]).value == "# Planning"
    else:
        assert event.rendered_content is None
    assert manager.get_cached_data("workflow_state").phase == "planning"
    assert manager.get_cached_data("workflow_change_content") is None


@pytest.mark.anyio
async def test_state_format_template_provides_strict_yaml_file_guidance(workflow_task):
    session, _, _, _ = workflow_task
    path = Path("src/mcp_guide/templates/_workflow/state-format.mustache")
    stat = path.stat()
    file_info = FileInfo(
        path=path,
        size=stat.st_size,
        content_size=stat.st_size,
        mtime=datetime.fromtimestamp(stat.st_mtime),
        name=path.name,
    )
    rendered = await render_template(
        session,
        file_info=file_info,
        base_dir=path.parent,
        project_flags={"workflow": True},
        context=TemplateContext({"workflow": {"file": ".guide.yaml"}}),
    )
    assert rendered is not None
    for text in (
        "# Workflow State File Format",
        "strictly valid YAML",
        "lowercase keys",
        "Optional lines may be omitted",
        "description: <optional-description>",
        "`send_file_content` MCP tool",
    ):
        assert text in rendered.content
