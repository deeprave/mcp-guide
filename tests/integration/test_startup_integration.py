"""Integration tests for startup instruction feature."""

import pytest

from mcp_guide.models.project import Category, Collection, Project
from mcp_guide.task_manager.manager import TaskManager
from mcp_guide.workflow.flags import parse_startup_expression, validate_startup_expression


class TestStartupValidation:
    """Test startup expression validation."""

    @pytest.fixture
    def project(self):
        """Create test project."""
        return Project(
            name="test-project",
            categories={
                "docs": Category(name="docs", dir="docs", patterns=["*.md"]),
                "examples": Category(name="examples", dir="examples", patterns=["*.py"]),
            },
            collections={
                "guidelines": Collection(name="guidelines", categories=["docs"]),
            },
        )

    def test_parse_single_category(self):
        """Parse single category expression."""
        categories, collections = parse_startup_expression("docs")
        assert categories == ["docs"]
        assert collections == []

    def test_parse_collection(self):
        """Parse collection expression."""
        categories, collections = parse_startup_expression("@guidelines")
        assert categories == []
        assert collections == ["guidelines"]

    def test_parse_mixed(self):
        """Parse mixed expression."""
        categories, collections = parse_startup_expression("docs,@guidelines,examples")
        assert categories == ["docs", "examples"]
        assert collections == ["guidelines"]

    def test_parse_with_pattern(self):
        """Parse expression with pattern."""
        categories, collections = parse_startup_expression("docs/README*")
        assert categories == ["docs"]
        assert collections == []

    def test_validate_valid_category(self, project):
        """Validate existing category."""
        result = validate_startup_expression("docs", project)
        assert result.success

    def test_validate_valid_collection(self, project):
        """Validate existing collection."""
        result = validate_startup_expression("@guidelines", project)
        assert result.success

    def test_validate_invalid_category(self, project):
        """Reject non-existent category."""
        result = validate_startup_expression("nonexistent", project)
        assert not result.success
        assert "category" in result.error.lower()

    def test_validate_invalid_collection(self, project):
        """Reject non-existent collection."""
        result = validate_startup_expression("@nonexistent", project)
        assert not result.success
        assert "collection" in result.error.lower()


class TestPriorityQueueing:
    """Test priority queueing in task manager."""

    @pytest.fixture
    async def task_manager(self):
        """Create task manager instance."""
        TaskManager._reset_for_testing()
        manager = TaskManager()
        yield manager
        TaskManager._reset_for_testing()

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
    async def test_deduplication_with_priority(self, task_manager):
        """Deduplication works with priority."""
        await task_manager.queue_instruction("instruction")
        await task_manager.queue_instruction("instruction", priority=True)

        instructions = task_manager._pending_instructions
        assert len(instructions) == 1
        assert instructions == ["instruction"]
