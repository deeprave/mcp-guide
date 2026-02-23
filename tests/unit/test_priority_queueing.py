"""Tests for priority queueing in task manager."""

import pytest

from mcp_guide.task_manager.manager import TaskManager


class TestPriorityQueueing:
    """Test priority parameter in queue_instruction."""

    @pytest.fixture
    async def task_manager(self):
        """Create task manager instance."""
        # Reset singleton state for clean test
        TaskManager._reset_for_testing()
        manager = TaskManager()
        yield manager
        # Clean up after test
        TaskManager._reset_for_testing()

    @pytest.mark.asyncio
    async def test_default_appends(self, task_manager):
        """Default priority=False appends to end."""
        await task_manager.queue_instruction("first")
        await task_manager.queue_instruction("second")
        await task_manager.queue_instruction("third")

        instructions = task_manager._pending_instructions
        assert instructions == ["first", "second", "third"]

    @pytest.mark.asyncio
    async def test_priority_inserts_at_front(self, task_manager):
        """Priority=True inserts at front."""
        await task_manager.queue_instruction("first")
        await task_manager.queue_instruction("urgent", priority=True)

        instructions = task_manager._pending_instructions
        assert instructions == ["urgent", "first"]

    @pytest.mark.asyncio
    async def test_multiple_priority_maintains_order(self, task_manager):
        """Multiple priority instructions maintain insertion order."""
        await task_manager.queue_instruction("first")
        await task_manager.queue_instruction("urgent1", priority=True)
        await task_manager.queue_instruction("urgent2", priority=True)

        instructions = task_manager._pending_instructions
        assert instructions == ["urgent2", "urgent1", "first"]

    @pytest.mark.asyncio
    async def test_mixed_priority_and_normal(self, task_manager):
        """Mixed priority and normal instructions."""
        await task_manager.queue_instruction("normal1")
        await task_manager.queue_instruction("urgent1", priority=True)
        await task_manager.queue_instruction("normal2")
        await task_manager.queue_instruction("urgent2", priority=True)

        instructions = task_manager._pending_instructions
        assert instructions == ["urgent2", "urgent1", "normal1", "normal2"]

    @pytest.mark.asyncio
    async def test_deduplication_still_works(self, task_manager):
        """Deduplication works with priority."""
        await task_manager.queue_instruction("instruction")
        await task_manager.queue_instruction("instruction", priority=True)

        instructions = task_manager._pending_instructions
        assert instructions == ["instruction"]
        assert len(instructions) == 1

    @pytest.mark.asyncio
    async def test_priority_false_explicit(self, task_manager):
        """Explicit priority=False behaves like default."""
        await task_manager.queue_instruction("first")
        await task_manager.queue_instruction("second", priority=False)

        instructions = task_manager._pending_instructions
        assert instructions == ["first", "second"]
