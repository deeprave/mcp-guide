"""Tests for TaskManager pub/sub functionality."""

from typing import Any

import pytest

from mcp_guide.task_manager import EventType, TaskManager


class MockSubscriber:
    """Mock subscriber for testing."""

    def __init__(self, name: str = "test"):
        self.name = name
        self.received_events = []

    def get_name(self) -> str:
        """Get subscriber name."""
        return self.name

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle events and record them."""
        self.received_events.append((event_type, data))
        return True


@pytest.fixture(autouse=True)
def reset_task_manager() -> None:
    """Reset TaskManager singleton before each test."""
    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class TestTaskManagerInstantiation:
    """Test TaskManager can be created."""

    def test_task_manager_can_be_instantiated(self) -> None:
        """TaskManager should be instantiable."""
        manager = TaskManager()
        assert manager is not None


class TestAgentDataInterception:
    """Test agent data interception and event dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_event_with_interest(self, task_manager: TaskManager, mock_task: MockSubscriber) -> None:
        """Test handling data with interested task."""
        task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        result = await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": "test.txt", "content": "data"})

        assert result == {"status": "processed"}
        # Check that handle_event was called with the correct data
        assert len(mock_task.received_events) == 1
        event_type, data = mock_task.received_events[0]
        assert event_type == EventType.FS_FILE_CONTENT
        assert data == {"path": "test.txt", "content": "data"}

    @pytest.mark.asyncio
    async def test_bit_flag_filtering(self, task_manager: TaskManager, mock_task: MockSubscriber) -> None:
        """Test bit-flag pre-filtering."""
        task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        # Dispatch different event type - should not be handled
        result = await task_manager.dispatch_event(EventType.FS_DIRECTORY, {"path": "test_dir"})

        assert result == {"status": "acknowledged"}
        assert len(mock_task.received_events) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self, task_manager: TaskManager) -> None:
        """Test multiple subscribers receiving the same event."""
        subscriber1 = MockSubscriber("sub1")
        subscriber2 = MockSubscriber("sub2")

        task_manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT)
        task_manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT)

        result = await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": "test.txt", "content": "data"})

        assert result == {"status": "processed"}
        assert len(subscriber1.received_events) == 1
        assert len(subscriber2.received_events) == 1


@pytest.fixture
def task_manager() -> TaskManager:
    """Create a fresh TaskManager for each test."""
    TaskManager._reset_for_testing()
    return TaskManager()


@pytest.fixture
def mock_task() -> MockSubscriber:
    """Create a mock task for testing."""
    return MockSubscriber()


class TestGetTaskByType:
    """Test get_task_by_type functionality."""

    def test_get_task_by_type_returns_correct_instance(self, task_manager: TaskManager) -> None:
        """Test get_task_by_type returns the correct subscriber instance."""
        subscriber = MockSubscriber("test-subscriber")
        task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT)

        result = task_manager.get_task_by_type(MockSubscriber)

        assert result is subscriber
        assert result.name == "test-subscriber"

    def test_get_task_by_type_returns_none_when_absent(self, task_manager: TaskManager) -> None:
        """Test get_task_by_type returns None when task type not registered."""
        result = task_manager.get_task_by_type(MockSubscriber)

        assert result is None

    def test_get_task_by_type_exact_match_only(self, task_manager: TaskManager) -> None:
        """Test get_task_by_type uses exact type matching, not isinstance."""

        class SubclassMock(MockSubscriber):
            pass

        base_subscriber = MockSubscriber("base")
        subclass_subscriber = SubclassMock("subclass")

        task_manager.subscribe(base_subscriber, EventType.FS_FILE_CONTENT)
        task_manager.subscribe(subclass_subscriber, EventType.FS_FILE_CONTENT)

        # Should return exact type match only
        result_base = task_manager.get_task_by_type(MockSubscriber)
        result_subclass = task_manager.get_task_by_type(SubclassMock)

        assert result_base is base_subscriber
        assert result_subclass is subclass_subscriber

    def test_get_task_by_type_multiple_instances_returns_first(
        self, task_manager: TaskManager, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test get_task_by_type returns first instance and logs warning when multiple exist."""
        subscriber1 = MockSubscriber("first")
        subscriber2 = MockSubscriber("second")

        task_manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT)
        task_manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT)

        result = task_manager.get_task_by_type(MockSubscriber)

        assert result is subscriber1
        assert "Multiple task subscribers found for type MockSubscriber" in caplog.text
