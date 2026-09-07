"""Task activation follows real project flags and the explicitly supplied session."""

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType, TaskManager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


@pytest.mark.anyio
async def test_task_activation_and_initialisation_use_the_supplied_project(runtime, tmp_path):
    templates = tmp_path / "docs" / "_openspec"
    templates.mkdir(parents=True)
    (templates / "openspec-cli-check.mustache").write_text("Check CLI for {{project.name}}")
    context_templates = templates.parent / "_context"
    context_templates.mkdir()
    (context_templates / "client-context-setup.mustache").write_text("Client information for {{project.name}}")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(templates.parent), "projects": {}})
    )
    await runtime.feature_flags().set("allow-client-info", True)
    enabled = await create_bound_test_session(runtime, "enabled")
    await enabled.project_flags().set("workflow", True)
    await enabled.project_flags().set("openspec", True)
    disabled = await create_bound_test_session(runtime, "disabled")

    manager = TaskManager(session=disabled)
    try:
        assert await manager.requires_flag("workflow", enabled) is True
        assert await manager.requires_flag("workflow", disabled) is False
        for task_class in (WorkflowMonitorTask, OpenSpecTask):
            task = task_class(task_manager=manager)
            assert await task.start(manager, disabled) is False
            assert manager.get_subscription_count() == 0
            assert await task.start(manager, enabled) is True
            assert manager.get_subscription_count() == 1
            if task_class is OpenSpecTask:
                result = await task.handle_event(EventType.TIMER_ONCE, {})
                assert result.result is True
                delivered = await manager.process_result(Result.ok())
                assert delivered.additional_agent_instructions == "Check CLI for enabled"
            await manager.unsubscribe(task)

        client_task = ClientContextTask(task_manager=manager)
        assert await client_task.start(manager, enabled) is True
        assert await client_task.start(manager, enabled) is True
        assert manager.get_subscription_count() == 1
        result = await client_task.handle_event(EventType.TIMER_ONCE, {})
        assert result.result is True
        delivered = await manager.process_result(Result.ok())
        assert delivered.additional_agent_instructions == "Client information for enabled"
        await manager.unsubscribe(client_task)
        await runtime.feature_flags().set("allow-client-info", False)
        # Flag publication restarts registered tasks; declining this task adds no subscription.
        subscriptions = manager.get_subscription_count()
        assert await ClientContextTask(task_manager=manager).start(manager, disabled) is False
        assert manager.get_subscription_count() == subscriptions
        for task_class in (ClientContextTask, OpenSpecTask):
            task = task_class(task_manager=manager)
            assert await task.start(manager, disabled) is False
            manager.subscribe(task, EventType.TIMER_ONCE)
            result = await task.handle_event(EventType.TIMER_ONCE, {})
            assert result.result is True
            assert manager.get_subscription_count() == subscriptions
    finally:
        await manager.cleanup()
