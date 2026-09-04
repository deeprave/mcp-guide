"""Tests for runtime project-scoped task activation policy."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.task_manager import EventType, TaskManager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


def _patch_resolved_flags(flags: dict[str, object]):
    """Patch flag resolution for task-owned activation tests."""
    return patch("mcp_guide.task_manager.manager.resolve_all_flags", new=AsyncMock(return_value=flags))


class TestRuntimeProjectTaskActivation:
    """Runtime tasks independently decide whether to subscribe."""

    @pytest.mark.anyio
    async def test_requires_flag_resolves_against_explicit_session(self) -> None:
        """Explicit lifecycle session wins over ambient ContextVar session."""
        task_manager = TaskManager()
        supplied_session = Mock()
        supplied_session.add_listener = Mock()
        ambient_session = Mock()
        ambient_session.add_listener = Mock()

        def resolve_flags(session: Mock) -> dict[str, bool]:
            return {"workflow": session is supplied_session}

        with (
            patch(
                "mcp_guide.runtime.GuideRuntime.create_session",
                new_callable=AsyncMock,
                return_value=ambient_session,
            ) as mock_get_session,
            patch(
                "mcp_guide.task_manager.manager.resolve_all_flags",
                new_callable=AsyncMock,
                side_effect=resolve_flags,
            ) as mock_resolve_flags,
        ):
            enabled = await task_manager.requires_flag("workflow", supplied_session)

        assert enabled is True
        mock_get_session.assert_not_awaited()
        mock_resolve_flags.assert_awaited_once_with(supplied_session)
        supplied_session.add_listener.assert_called_once_with(task_manager)
        ambient_session.add_listener.assert_not_called()

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "task_cls, flag_name",
        [
            (WorkflowMonitorTask, "workflow"),
            (ClientContextTask, "allow-client-info"),
            (OpenSpecTask, "openspec"),
        ],
    )
    async def test_task_start_resolves_flags_from_supplied_session(self, task_cls, flag_name: str) -> None:
        """Project-scoped task startup uses the notified session, not ambient session."""
        task_manager = TaskManager()
        task = task_cls(task_manager=task_manager)
        supplied_session = Mock()
        supplied_session.add_listener = Mock()
        ambient_session = Mock()
        ambient_session.add_listener = Mock()

        def resolve_flags(session: Mock) -> dict[str, bool]:
            return {flag_name: session is supplied_session}

        with (
            patch(
                "mcp_guide.runtime.GuideRuntime.create_session",
                new_callable=AsyncMock,
                return_value=ambient_session,
            ) as mock_get_session,
            patch(
                "mcp_guide.task_manager.manager.resolve_all_flags",
                new_callable=AsyncMock,
                side_effect=resolve_flags,
            ),
        ):
            started = await task.start(task_manager, supplied_session)

        assert started is True
        mock_get_session.assert_not_awaited()
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_openspec_initialise_reads_project_from_supplied_session(self) -> None:
        """Deferred OpenSpec project reads stay tied to the lifecycle session."""
        task_manager = TaskManager()
        task = OpenSpecTask(task_manager=task_manager)
        supplied_session = Mock()
        supplied_session.add_listener = Mock()
        supplied_session.get_project = AsyncMock(
            return_value=SimpleNamespace(openspec_version="1.2.3", openspec_validated=False)
        )
        ambient_session = Mock()
        ambient_session.add_listener = Mock()
        ambient_session.get_project = AsyncMock(
            return_value=SimpleNamespace(openspec_version="9.9.9", openspec_validated=False)
        )

        def resolve_flags(session: Mock) -> dict[str, bool]:
            return {"openspec": session is supplied_session}

        with (
            patch(
                "mcp_guide.runtime.GuideRuntime.create_session",
                new_callable=AsyncMock,
                return_value=ambient_session,
            ) as mock_get_session,
            patch(
                "mcp_guide.task_manager.manager.resolve_all_flags",
                new_callable=AsyncMock,
                side_effect=resolve_flags,
            ),
            patch.object(task, "request_cli_check", new_callable=AsyncMock),
        ):
            started = await task.start(task_manager, supplied_session)
            result = await task.handle_event(EventType.TIMER_ONCE, {})

        assert started is True
        assert result is not None
        assert result.result is True
        mock_get_session.assert_not_awaited()
        supplied_session.get_project.assert_awaited_once()
        ambient_session.get_project.assert_not_awaited()
        assert task_manager.get_cached_data("openspec_version") == "1.2.3"

    @pytest.mark.anyio
    async def test_workflow_task_subscribes_when_workflow_enabled(self) -> None:
        """Workflow activation is owned by WorkflowMonitorTask."""
        task_manager = TaskManager()
        task = WorkflowMonitorTask(task_manager=task_manager)

        with _patch_resolved_flags({"workflow": True}):
            started = await task.start(task_manager, Mock())

        assert started is True
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_workflow_task_stays_inactive_when_workflow_disabled(self) -> None:
        """Workflow task can decline activation without task-manager flag policy."""
        task_manager = TaskManager()
        task = WorkflowMonitorTask(task_manager=task_manager)

        with _patch_resolved_flags({"workflow": False}):
            started = await task.start(task_manager, Mock())

        assert started is False
        assert task_manager.get_subscription_count() == 0

    @pytest.mark.anyio
    async def test_client_context_task_owns_allow_client_info_policy(self) -> None:
        """Client context activation is independent of workflow/OpenSpec."""
        task_manager = TaskManager()
        task = ClientContextTask(task_manager=task_manager)

        with _patch_resolved_flags({"allow-client-info": True}):
            started = await task.start(task_manager, Mock())

        assert started is True
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_openspec_task_owns_openspec_policy(self) -> None:
        """OpenSpec activation is independent of workflow/client-info."""
        task_manager = TaskManager()
        task = OpenSpecTask(task_manager=task_manager)

        with _patch_resolved_flags({"openspec": True}):
            started = await task.start(task_manager, Mock())

        assert started is True
        assert task_manager.get_subscription_count() == 1
