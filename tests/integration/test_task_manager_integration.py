"""Minimal test without fixtures."""

import asyncio

from mcp_guide.task_manager import get_task_manager


def test_task_manager_initialization():
    """Test TaskManager can be initialized."""
    task_manager = get_task_manager()
    assert task_manager is not None


def test_instruction_acknowledgement_api():
    """Test instruction acknowledgement public API."""

    async def run_test():
        manager = get_task_manager()

        # Queue with tracking - returns ID
        instruction_id = await manager.queue_instruction_with_ack("Test retry")

        # Acknowledge it - should stop retry
        await manager.acknowledge_instruction(instruction_id)

        # Queue another one without acknowledging
        instruction_id2 = await manager.queue_instruction_with_ack("Test retry 2", max_retries=1)

        # Verify public API works
        assert instruction_id is not None
        assert instruction_id2 is not None

    asyncio.run(run_test())
