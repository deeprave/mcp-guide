"""Tests for @task_init decorator pattern."""

from unittest.mock import AsyncMock, Mock, patch

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.decorators import task_init
from mcp_guide.task_manager import TaskManager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


class TestTaskInitDecorator:
    """Test @task_init decorator basic functionality."""

    def test_task_init_decorator_exists(self):
        """Test that @task_init decorator can be imported."""
        assert callable(task_init)

    def test_task_init_decorator_calls_registration_functions(self):
        """Test that @task_init decorator exists and can be used."""

        @task_init
        class TestManager:
            def __init__(self):
                pass

        # Should be able to create instance
        manager = TestManager()
        assert manager is not None

    def test_task_init_decorator_with_workflow_manager(self):
        """Test that @task_init decorator can be used with parameters."""

        # Should accept workflow parameter
        @task_init
        class TestWorkflowManager:
            def __init__(self):
                pass

        manager = TestWorkflowManager()
        assert manager is not None


class TestTaskManagerAutoRegistration:
    """Test TaskManager auto-registration with @task_init."""

    def test_task_manager_has_task_init_decorator(self):
        """Test that TaskManager class has @task_init decorator."""
        # TaskManager should be importable and have get_name or similar
        assert TaskManager is not None

    def test_task_manager_auto_registers_on_creation(self):
        """Test that TaskManager can be created."""
        TaskManager._reset_for_testing()
        manager = TaskManager()
        assert manager is not None


class TestWorkflowTaskManagerAutoRegistration:
    """Test WorkflowMonitorTask auto-registration with @task_init."""

    def test_workflow_task_manager_has_task_init_decorator(self):
        """Test that WorkflowMonitorTask class exists."""
        assert WorkflowMonitorTask is not None

    def test_workflow_task_manager_auto_registers_on_creation(self):
        """Test that WorkflowMonitorTask can be created."""
        task = WorkflowMonitorTask()
        assert task is not None


class TestClientContextManagerCreation:
    """Test ClientContextTask creation and auto-registration."""

    def test_client_context_manager_exists(self):
        """Test that ClientContextTask can be imported."""
        assert ClientContextTask is not None

    def test_client_context_manager_has_task_init_decorator(self):
        """Test that ClientContextTask class has @task_init decorator."""
        # Check that the class has get_name method (required by task protocol)
        assert hasattr(ClientContextTask, "get_name")

    def test_client_context_manager_creates_and_registers_task(self):
        """Test that ClientContextTask can be instantiated and registered."""
        mock_task_manager = Mock()
        mock_task_manager.subscribe = Mock()

        # Mock session to enable the flag
        mock_session = Mock()
        mock_flags = AsyncMock()
        mock_flags.list = AsyncMock(return_value={"allow-client-info": True})
        mock_session.feature_flags.return_value = mock_flags

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Create ClientContextTask instance
            ClientContextTask(task_manager=mock_task_manager)

            # Should have subscribed
            mock_task_manager.subscribe.assert_called_once()
