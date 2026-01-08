"""Minimal test without fixtures."""


def test_minimal():
    """Minimal test."""
    print("Test starting...")

    from mcp_guide.task_manager import get_task_manager

    print("Import OK")

    task_manager = get_task_manager()
    print("TaskManager OK")

    assert task_manager is not None
    print("Test complete")
