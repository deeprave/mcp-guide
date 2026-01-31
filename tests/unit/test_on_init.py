"""Tests for @guide.on_init() decorator and initialization flow."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.render.content import RenderedContent
from mcp_guide.utils.frontmatter import Frontmatter


def make_rendered_content(content: str, instruction: str | None = None) -> RenderedContent:
    """Helper to create RenderedContent for mocking."""
    return RenderedContent(
        content=content,
        frontmatter=Frontmatter({"instruction": instruction} if instruction else {}),
        template_path=Path("test.mustache"),
        template_name="test",
        frontmatter_length=0,
        content_length=len(content),
    )


class TestOnInitDecorator:
    """Test @guide.on_init() decorator functionality."""

    def test_on_init_decorator_registers_handler(self):
        """Test that @guide.on_init() registers startup handlers."""
        from mcp_guide.guide import GuideMCP

        guide = GuideMCP("test")

        handler_called = False

        @guide.on_init()
        async def test_handler():
            nonlocal handler_called
            handler_called = True

        assert len(guide._startup_handlers) == 1
        assert guide._startup_handlers[0] == test_handler

    def test_on_init_decorator_multiple_handlers(self):
        """Test that multiple handlers can be registered."""
        from mcp_guide.guide import GuideMCP

        guide = GuideMCP("test")

        @guide.on_init()
        async def handler1():
            pass

        @guide.on_init()
        async def handler2():
            pass

        assert len(guide._startup_handlers) == 2


class TestLifespanExecution:
    """Test guide_lifespan() context manager execution."""

    @pytest.mark.asyncio
    async def test_lifespan_executes_handlers(self):
        """Test that lifespan executes all registered handlers."""
        from mcp_guide.guide import GuideMCP
        from mcp_guide.server import guide_lifespan

        guide = GuideMCP("test")

        handler1_called = False
        handler2_called = False

        @guide.on_init()
        async def handler1():
            nonlocal handler1_called
            handler1_called = True

        @guide.on_init()
        async def handler2():
            nonlocal handler2_called
            handler2_called = True

        async with guide_lifespan(guide):
            pass

        assert handler1_called
        assert handler2_called

    @pytest.mark.asyncio
    async def test_lifespan_continues_on_handler_error(self):
        """Test that lifespan continues executing handlers even if one fails."""
        from mcp_guide.guide import GuideMCP
        from mcp_guide.server import guide_lifespan

        guide = GuideMCP("test")

        handler2_called = False

        @guide.on_init()
        async def failing_handler():
            raise RuntimeError("Test error")

        @guide.on_init()
        async def handler2():
            nonlocal handler2_called
            handler2_called = True

        async with guide_lifespan(guide):
            pass

        # Second handler should still execute
        assert handler2_called


class TestTaskManagerOnInit:
    """Test TaskManager.on_init() method."""

    @pytest.mark.asyncio
    async def test_task_manager_requires_flag_returns_true_when_enabled(self):
        """Test that requires_flag() returns True when flag is enabled."""
        from mcp_guide.task_manager.manager import TaskManager

        TaskManager._reset_for_testing()
        task_manager = TaskManager()
        task_manager._resolved_flags = {"test-flag": True}

        assert task_manager.requires_flag("test-flag") is True

    @pytest.mark.asyncio
    async def test_task_manager_requires_flag_returns_false_when_disabled(self):
        """Test that requires_flag() returns False when flag is disabled."""
        from mcp_guide.task_manager.manager import TaskManager

        TaskManager._reset_for_testing()
        task_manager = TaskManager()
        task_manager._resolved_flags = {"test-flag": False}

        assert task_manager.requires_flag("test-flag") is False

    @pytest.mark.asyncio
    async def test_task_manager_requires_flag_returns_false_when_missing(self):
        """Test that requires_flag() returns False when flag is not set."""
        from mcp_guide.task_manager.manager import TaskManager

        TaskManager._reset_for_testing()
        task_manager = TaskManager()
        task_manager._resolved_flags = {}

        assert task_manager.requires_flag("test-flag") is False

    @pytest.mark.asyncio
    async def test_task_manager_on_init_establishes_session(self):
        """Test that TaskManager.on_init() establishes session."""
        from mcp_guide.task_manager.manager import TaskManager

        TaskManager._reset_for_testing()
        task_manager = TaskManager()

        with (
            patch("mcp_guide.session.get_or_create_session", new_callable=AsyncMock) as mock_session,
            patch("mcp_guide.models.resolve_all_flags", return_value={}),
        ):
            mock_session.return_value = Mock(pwd="/test/path")

            await task_manager.on_init()

            mock_session.assert_called_once()
            assert task_manager.session is not None

    @pytest.mark.asyncio
    async def test_task_manager_on_init_calls_task_on_init(self):
        """Test that TaskManager.on_init() calls on_init() on registered tasks."""
        from mcp_guide.task_manager.manager import TaskManager
        from mcp_guide.task_manager.subscription import Subscription

        TaskManager._reset_for_testing()
        task_manager = TaskManager()

        mock_task = Mock()
        mock_task.on_init = AsyncMock()
        mock_task.get_name = Mock(return_value="MockTask")

        # Create a subscription for the mock task
        subscription = Subscription(mock_task, 0, None, None)
        task_manager._subscriptions.append(subscription)

        with (
            patch("mcp_guide.session.get_or_create_session", new_callable=AsyncMock) as mock_session,
            patch("mcp_guide.models.resolve_all_flags", return_value={}),
        ):
            mock_session.return_value = Mock(pwd="/test/path", project_name="test")

            await task_manager.on_init()

            mock_task.on_init.assert_called_once()


class TestTaskOnInit:
    """Test task on_init() implementations."""

    @pytest.mark.asyncio
    async def test_openspec_task_on_init_checks_flag(self):
        """Test that OpenSpecTask.on_init() checks flag and unsubscribes if disabled."""
        from mcp_guide.openspec.task import OpenSpecTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = Mock(return_value=False)
        mock_task_manager.unsubscribe = AsyncMock()

        task = OpenSpecTask(task_manager=mock_task_manager)
        await task.on_init()

        mock_task_manager.requires_flag.assert_called_once_with("openspec")
        mock_task_manager.unsubscribe.assert_called_once_with(task)
        assert task._flag_checked

    @pytest.mark.asyncio
    async def test_workflow_task_on_init_queues_setup(self):
        """Test that WorkflowMonitorTask.on_init() queues setup instruction when enabled."""
        from mcp_guide.workflow.tasks import WorkflowMonitorTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = Mock(return_value=True)
        mock_task_manager.queue_instruction = AsyncMock()

        with patch("mcp_guide.workflow.tasks.render_workflow_template") as mock_render:
            mock_render.return_value = make_rendered_content("setup content")

            task = WorkflowMonitorTask()
            task.task_manager = mock_task_manager

            await task.on_init()

            mock_task_manager.requires_flag.assert_called_once_with("workflow")
            mock_render.assert_called_once_with("monitoring-setup")
            mock_task_manager.queue_instruction.assert_called_once_with("setup content")
            assert task._setup_done

    @pytest.mark.asyncio
    async def test_workflow_task_on_init_unsubscribes_when_disabled(self):
        """Test that WorkflowMonitorTask.on_init() unsubscribes when flag is disabled."""
        from mcp_guide.workflow.tasks import WorkflowMonitorTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = Mock(return_value=False)
        mock_task_manager.unsubscribe = AsyncMock()

        task = WorkflowMonitorTask()
        task.task_manager = mock_task_manager

        await task.on_init()

        mock_task_manager.requires_flag.assert_called_once_with("workflow")
        mock_task_manager.unsubscribe.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_client_context_task_on_init_requests_info_when_enabled(self):
        """Test that ClientContextTask.on_init() requests OS info when flag is enabled."""
        from mcp_guide.context.tasks import ClientContextTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = Mock(return_value=True)
        mock_task_manager.queue_instruction = AsyncMock()

        with patch("mcp_guide.context.tasks.render_context_template") as mock_render:
            mock_render.return_value = "client context setup"

            task = ClientContextTask(task_manager=mock_task_manager)
            await task.on_init()

            mock_task_manager.requires_flag.assert_called_once_with("allow-client-info")
            mock_render.assert_called_once_with("client-context-setup")
            mock_task_manager.queue_instruction.assert_called_once_with("client context setup")
            assert task._os_info_requested
            assert task._flag_checked

    @pytest.mark.asyncio
    async def test_client_context_task_on_init_unsubscribes_when_disabled(self):
        """Test that ClientContextTask.on_init() unsubscribes when flag is disabled."""
        from mcp_guide.context.tasks import ClientContextTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = Mock(return_value=False)
        mock_task_manager.unsubscribe = AsyncMock()

        task = ClientContextTask(task_manager=mock_task_manager)
        await task.on_init()

        mock_task_manager.requires_flag.assert_called_once_with("allow-client-info")
        mock_task_manager.unsubscribe.assert_called_once_with(task)
        assert task._flag_checked
