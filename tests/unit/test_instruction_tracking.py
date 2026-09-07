"""Behavioural coverage for instruction delivery, acknowledgement and retries."""

import pytest

from mcp_guide.result import Result


@pytest.mark.anyio
async def test_acknowledged_delivery_deduplicates_and_stops_retrying(task_manager, monkeypatch):
    now = 100.0
    monkeypatch.setattr("mcp_guide.task_manager.manager.time.time", lambda: now)
    assert task_manager.is_queue_empty()
    instruction_id = await task_manager.queue_instruction_with_ack("Read the file")
    assert instruction_id
    assert await task_manager.queue_instruction_with_ack("Read the file") == instruction_id
    assert not task_manager.is_queue_empty()
    delivered = await task_manager.process_result(Result.ok())
    assert delivered.additional_agent_instructions == "Read the file"
    assert task_manager.is_queue_empty()

    await task_manager.acknowledge_instruction(instruction_id)
    await task_manager.acknowledge_instruction("unknown")
    now += 31
    await task_manager.retry_unacknowledged()
    assert task_manager.is_queue_empty()
    assert (await task_manager.process_result(Result.ok())).additional_agent_instructions is None


@pytest.mark.anyio
async def test_retry_delay_urgency_and_original_limit(task_manager, monkeypatch):
    now = 100.0
    monkeypatch.setattr("mcp_guide.task_manager.manager.time.time", lambda: now)
    instruction_id = await task_manager.queue_instruction_with_ack("Read the file", max_retries=3)
    assert await task_manager.queue_instruction_with_ack("Read the file", max_retries=1) == instruction_id
    assert (await task_manager.process_result(Result.ok())).additional_agent_instructions == "Read the file"

    now += 29
    await task_manager.retry_unacknowledged()
    assert task_manager.is_queue_empty()

    for expected in ("Read the file", "**IMPORTANT:** Read the file", "**URGENT:** Read the file"):
        now += 31
        await task_manager.retry_unacknowledged()
        assert (await task_manager.process_result(Result.ok())).additional_agent_instructions == expected
        assert task_manager.is_queue_empty()

    now += 31
    await task_manager.retry_unacknowledged()
    assert task_manager.is_queue_empty()
    now += 31
    await task_manager.retry_unacknowledged()
    assert task_manager.is_queue_empty()
