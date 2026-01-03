"""Tests for workflow manager integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_guide.task_manager import TaskManager
from mcp_guide.workflow.manager import WorkflowManager


class TestWorkflowManager:
    """Test WorkflowManager functionality."""

    @pytest.fixture
    def task_manager(self):
        """Create TaskManager instance."""
        task_manager = TaskManager()
        task_manager.register_task = AsyncMock()
        task_manager.register_interest = MagicMock()
        task_manager.complete_task = MagicMock()
        return task_manager

    @pytest.fixture
    def project_flags(self):
        """Create mock ProjectFlags instance."""
        flags = MagicMock()
        flags.get = AsyncMock()
        return flags

    @pytest.fixture
    def workflow_manager(self, task_manager, project_flags):
        """Create WorkflowManager instance."""
        return WorkflowManager(task_manager, project_flags)

    async def test_is_workflow_enabled_true(self, workflow_manager, project_flags):
        """Test workflow enabled when flag is set."""
        project_flags.get.return_value = "workflow-state.json"
        result = await workflow_manager.is_workflow_enabled()
        assert result is True

    async def test_is_workflow_enabled_false(self, workflow_manager, project_flags):
        """Test workflow disabled when flag is None."""
        project_flags.get.return_value = None
        result = await workflow_manager.is_workflow_enabled()
        assert result is False

    async def test_start_monitoring_when_enabled(self, workflow_manager, project_flags, task_manager):
        """Test start monitoring creates and registers monitor task."""
        project_flags.get.return_value = "workflow-state.json"

        await workflow_manager.start_monitoring()

        assert workflow_manager._monitor_task is not None
        task_manager.register_interest.assert_called_once()
        task_manager.register_task.assert_called_once()

    async def test_start_monitoring_when_disabled(self, workflow_manager, project_flags, task_manager):
        """Test start monitoring does nothing when disabled."""
        project_flags.get.return_value = None

        await workflow_manager.start_monitoring()

        assert workflow_manager._monitor_task is None
        task_manager.register_interest.assert_not_called()
        task_manager.register_task.assert_not_called()

    async def test_start_update_task(self, workflow_manager, project_flags, task_manager):
        """Test start update task creates and registers update task."""
        project_flags.get.return_value = "workflow-state.json"

        await workflow_manager.start_update_task("openspec/changes/test-component")

        assert workflow_manager._update_task is not None
        task_manager.register_interest.assert_called_once()
        task_manager.register_task.assert_called_once()

    async def test_start_update_task_replaces_existing(self, workflow_manager, project_flags, task_manager):
        """Test start update task completes existing task first."""
        project_flags.get.return_value = "workflow-state.json"

        # Start first task
        await workflow_manager.start_update_task("component1")
        first_task = workflow_manager._update_task

        # Start second task
        await workflow_manager.start_update_task("component2")

        # Should complete first task and create new one
        task_manager.complete_task.assert_called_with(first_task)
        assert workflow_manager._update_task != first_task

    def test_stop_monitoring(self, workflow_manager, task_manager):
        """Test stop monitoring completes monitor task."""
        # Set up monitor task
        workflow_manager._monitor_task = MagicMock()

        workflow_manager.stop_monitoring()

        task_manager.complete_task.assert_called_once()
        assert workflow_manager._monitor_task is None

    def test_stop_update_task(self, workflow_manager, task_manager):
        """Test stop update task completes update task."""
        # Set up update task
        workflow_manager._update_task = MagicMock()

        workflow_manager.stop_update_task()

        task_manager.complete_task.assert_called_once()
        assert workflow_manager._update_task is None
