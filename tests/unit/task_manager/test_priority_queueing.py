"""Queued instructions retain priority, ordering and deduplication on delivery."""

import pytest

from mcp_guide.result import Result


@pytest.mark.anyio
async def test_priority_order_and_deduplication_on_delivery(task_manager):
    await task_manager.queue_instruction("normal1")
    await task_manager.queue_instruction("urgent1", priority=True)
    await task_manager.queue_instruction("normal2", priority=False)
    await task_manager.queue_instruction("urgent2", priority=True)
    await task_manager.queue_instruction("normal1", priority=True)

    delivered = [(await task_manager.process_result(Result.ok())).additional_agent_instructions for _ in range(4)]
    assert delivered == ["urgent2", "urgent1", "normal1", "normal2"]
    assert task_manager.is_queue_empty()
    assert (await task_manager.process_result(Result.ok())).additional_agent_instructions is None
