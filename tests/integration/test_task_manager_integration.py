"""Integration coverage for Session-owned task manager operations."""

import pytest

from tests.helpers import create_test_session


@pytest.mark.anyio
async def test_instruction_acknowledgement_api(tmp_path):
    """Test instruction acknowledgement public API."""
    session = await create_test_session("task-manager", _config_dir_for_tests=str(tmp_path))
    manager = session.task_manager

    # Queue with tracking - returns ID
    instruction_id = await manager.queue_instruction_with_ack("Test retry")

    # Acknowledge it - should stop retry
    await manager.acknowledge_instruction(instruction_id)

    # Queue another one without acknowledging
    instruction_id2 = await manager.queue_instruction_with_ack("Test retry 2", max_retries=1)

    # Verify public API works
    assert instruction_id is not None
    assert instruction_id2 is not None
