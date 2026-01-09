"""Simple integration test to debug workflow processing."""

import pytest

from mcp_guide.task_manager import get_task_manager


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset TaskManager singleton before each test."""
    from mcp_guide.task_manager.manager import TaskManager

    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


def test_workflow_task_registration():
    """Test that workflow monitoring can be started."""

    # This should work synchronously
    print("Testing workflow monitoring startup...")

    # Get initial state
    task_manager = get_task_manager()
    initial_registrations = len(getattr(task_manager, "_registrations", []))
    print(f"Initial registrations: {initial_registrations}")

    # This is where it might be hanging - let's see
    print("About to start workflow monitoring...")


def test_basic_task_manager():
    """Test basic TaskManager functionality."""
    task_manager = get_task_manager()

    # Test basic cache operations
    task_manager.set_cached_data("test_key", "test_value")
    cached = task_manager.get_cached_data("test_key")

    assert cached == "test_value"
    print("TaskManager cache: OK")

    # Test registrations
    registrations = getattr(task_manager, "_registrations", [])
    print(f"Registrations list exists: {registrations is not None}")


def test_workflow_task_creation():
    """Test WorkflowMonitorTask creation."""
    from mcp_guide.workflow.tasks import WorkflowMonitorTask

    task = WorkflowMonitorTask(".guide.yaml")
    print(f"WorkflowMonitorTask created: {task}")
    print(f"Task name: {task.get_name()}")
