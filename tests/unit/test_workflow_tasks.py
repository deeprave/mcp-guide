"""Workflow task behaviour through real rendering, state and instructions."""

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.task_manager import EventType
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
async def test_accepts_known_phase_disabled_by_project_workflow_configuration(workflow_task):
    """A recognised workflow phase remains valid outside the configured sequence."""
    session, manager, _, templates = workflow_task
    await session.project_flags().set("workflow", ["discussion", "implementation"])
    task = manager.get_task_by_type(WorkflowMonitorTask)
    assert task is not None
    (templates / "state-format.mustache").write_text("Workflow received")

    event = await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "phase: planning\n"})

    assert event is not None
    assert event.result is True
    assert manager.get_cached_data("workflow_state").phase == "planning"
