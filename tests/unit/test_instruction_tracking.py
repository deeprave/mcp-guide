"""Tests for instruction tracking functionality."""

import time

import pytest

from mcp_guide.task_manager.manager import TaskManager, TrackedInstruction


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset TaskManager singleton between tests."""
    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class TestTrackedInstruction:
    """Test TrackedInstruction dataclass."""

    def test_tracked_instruction_creation(self):
        """Test creating a TrackedInstruction."""
        current_time = time.time()
        instr = TrackedInstruction(
            id="test-id",
            content="Test instruction",
            queued_at=current_time,
            last_sent_at=current_time,
            retry_count=0,
            max_retries=3,
        )

        assert instr.id == "test-id"
        assert instr.content == "Test instruction"
        assert instr.retry_count == 0
        assert instr.max_retries == 3
        assert isinstance(instr.queued_at, float)
        assert isinstance(instr.last_sent_at, float)

    def test_tracked_instruction_defaults(self):
        """Test TrackedInstruction default values."""
        current_time = time.time()
        instr = TrackedInstruction(id="test-id", content="Test", queued_at=current_time, last_sent_at=current_time)

        assert instr.retry_count == 0
        assert instr.max_retries == 3


class TestTaskManagerTracking:
    """Test TaskManager instruction tracking."""

    def test_tracking_dictionaries_initialized(self):
        """Test that tracking dictionaries are initialized empty."""
        manager = TaskManager()

        assert hasattr(manager, "_tracked_instructions")
        assert isinstance(manager._tracked_instructions, dict)
        assert len(manager._tracked_instructions) == 0

    @pytest.mark.anyio
    async def test_queue_instruction_with_ack_returns_id(self):
        """Test that queue_instruction_with_ack returns a unique ID."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction")

        assert isinstance(instruction_id, str)
        assert len(instruction_id) > 0

    @pytest.mark.anyio
    async def test_queue_instruction_with_ack_stores_tracking(self):
        """Test that queue_instruction_with_ack stores tracking metadata."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction", max_retries=5)

        assert instruction_id in manager._tracked_instructions
        tracked = manager._tracked_instructions[instruction_id]
        assert tracked.id == instruction_id
        assert tracked.content == "Test instruction"
        assert tracked.retry_count == 0
        assert tracked.max_retries == 5
        assert isinstance(tracked.queued_at, float)

    @pytest.mark.anyio
    async def test_queue_instruction_with_ack_adds_to_queue(self):
        """Test that queue_instruction_with_ack adds instruction to pending queue."""
        manager = TaskManager()

        await manager.queue_instruction_with_ack("Test instruction")

        assert "Test instruction" in manager._pending_instructions

    @pytest.mark.anyio
    async def test_queue_instruction_with_ack_deduplication(self):
        """Test that duplicate content returns same ID."""
        manager = TaskManager()

        id1 = await manager.queue_instruction_with_ack("Same content")
        id2 = await manager.queue_instruction_with_ack("Same content")

        assert id1 == id2
        assert len(manager._tracked_instructions) == 1
        # Should only be queued once
        assert manager._pending_instructions.count("Same content") == 1

    @pytest.mark.anyio
    async def test_acknowledge_instruction_removes_tracking(self):
        """Test that acknowledge_instruction removes instruction from tracking."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction")
        await manager.acknowledge_instruction(instruction_id)

        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_acknowledge_instruction_handles_nonexistent_id(self):
        """Test that acknowledge_instruction handles non-existent ID gracefully."""
        manager = TaskManager()

        # Should not raise exception
        await manager.acknowledge_instruction("nonexistent-id")

    def test_is_queue_empty_when_empty(self):
        """Test is_queue_empty returns True when queue is empty."""
        manager = TaskManager()

        assert manager.is_queue_empty() is True

    @pytest.mark.anyio
    async def test_is_queue_empty_when_not_empty(self):
        """Test is_queue_empty returns False when queue has instructions."""
        manager = TaskManager()

        await manager.queue_instruction("Test instruction")

        assert manager.is_queue_empty() is False

    @pytest.mark.anyio
    async def test_retry_unacknowledged_requeues_instructions(self):
        """Test that retry_unacknowledged requeues unacknowledged instructions."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction")
        # Clear the queue to simulate it being dispatched
        manager._pending_instructions.clear()

        # Set last_sent_at to past to allow immediate retry
        tracked = manager._tracked_instructions[instruction_id]
        tracked.last_sent_at = time.time() - 31.0

        await manager.retry_unacknowledged()

        assert "Test instruction" in manager._pending_instructions

    @pytest.mark.anyio
    async def test_retry_unacknowledged_increments_retry_count(self):
        """Test that retry_unacknowledged increments retry counter."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction")
        manager._pending_instructions.clear()

        # Set last_sent_at to past to allow immediate retry
        tracked = manager._tracked_instructions[instruction_id]
        tracked.last_sent_at = time.time() - 31.0

        await manager.retry_unacknowledged()

        tracked = manager._tracked_instructions[instruction_id]
        assert tracked.retry_count == 1

    @pytest.mark.anyio
    async def test_retry_unacknowledged_adds_urgency_prefix(self):
        """Test that retry_unacknowledged adds urgency prefix based on retry count."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction")
        manager._pending_instructions.clear()

        tracked = manager._tracked_instructions[instruction_id]

        # First retry - no prefix
        tracked.last_sent_at = time.time() - 31.0
        await manager.retry_unacknowledged()
        assert "Test instruction" in manager._pending_instructions
        manager._pending_instructions.clear()

        # Second retry - IMPORTANT prefix
        tracked.last_sent_at = time.time() - 31.0
        await manager.retry_unacknowledged()
        assert "**IMPORTANT:** Test instruction" in manager._pending_instructions
        manager._pending_instructions.clear()

        # Third retry - URGENT prefix
        tracked.last_sent_at = time.time() - 31.0
        await manager.retry_unacknowledged()
        assert "**URGENT:** Test instruction" in manager._pending_instructions

    @pytest.mark.anyio
    async def test_retry_unacknowledged_removes_after_max_retries(self):
        """Test that retry_unacknowledged removes instruction after max retries."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction", max_retries=2)
        manager._pending_instructions.clear()

        # Set last_sent_at to past to allow immediate retry
        tracked = manager._tracked_instructions[instruction_id]
        tracked.last_sent_at = time.time() - 31.0

        # Retry 3 times (exceeds max_retries=2)
        await manager.retry_unacknowledged()
        tracked.last_sent_at = time.time() - 31.0
        manager._pending_instructions.clear()
        await manager.retry_unacknowledged()
        tracked.last_sent_at = time.time() - 31.0
        manager._pending_instructions.clear()
        await manager.retry_unacknowledged()

        # Should be removed from tracking
        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_retry_unacknowledged_respects_minimum_delay(self):
        """Test that retry_unacknowledged waits 30 seconds before retry."""
        manager = TaskManager()

        instruction_id = await manager.queue_instruction_with_ack("Test instruction")
        manager._pending_instructions.clear()

        # Try to retry immediately - should not retry
        await manager.retry_unacknowledged()
        assert len(manager._pending_instructions) == 0

        # Set last_sent_at to 31 seconds ago - should retry
        tracked = manager._tracked_instructions[instruction_id]
        tracked.last_sent_at = time.time() - 31.0
        await manager.retry_unacknowledged()
        assert "Test instruction" in manager._pending_instructions
