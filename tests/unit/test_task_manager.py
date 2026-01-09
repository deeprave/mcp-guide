"""Tests for TaskManager core infrastructure."""

import asyncio
from typing import Any, Generator
from unittest.mock import AsyncMock

import pytest

from mcp_core.result import Result
from mcp_guide.task_manager import EventType, TaskManager, TaskState, TaskType


@pytest.fixture(autouse=True)
def reset_task_manager() -> Generator[None, None, None]:
    """Reset TaskManager singleton before each test."""
    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class MockTask:
    """Mock task for testing."""

    def __init__(self, timeout: float | None = None, task_type: TaskType = TaskType.ACTIVE):
        self.timeout = timeout
        self.task_type = task_type
        self.task_start_called = False
        self.timeout_expired_called = False
        self.paused = False
        self.process_data = AsyncMock()
        self.process_result = AsyncMock()
        self.received_events: list[tuple[EventType, dict[str, Any]]] = []
        self.handle_event_return = True

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle events and record them."""
        self.received_events.append((event_type, data))
        # Allow configurable return value for testing
        return getattr(self, "handle_event_return", True)

    async def task_start(self) -> tuple[TaskState, str | None]:
        """Start the task."""
        self.task_start_called = True
        return (TaskState.ACTIVE, None)

    async def pause(self) -> None:
        """Pause the task."""
        self.paused = True

    async def resume(self) -> None:
        """Resume the task."""
        self.paused = False

    async def response(self, data: Any) -> tuple[TaskState, str | None]:
        """Handle response data."""
        return (TaskState.COMPLETED, None)

    async def timeout_expired(self) -> tuple[TaskState, str | None]:
        """Handle timeout expiry."""
        self.timeout_expired_called = True
        return (TaskState.IDLE, None)

    async def completed(self) -> tuple[TaskState, str | None]:
        """Handle task completion."""
        return (TaskState.IDLE, None)

    def _is_workflow_file_result(self, result: "Result[Any]") -> bool:
        """Check if result is a workflow file result."""
        return True  # For testing, always return True


class TestTaskManagerInstantiation:
    """Test TaskManager can be created."""

    def test_task_manager_can_be_instantiated(self) -> None:
        """TaskManager should be instantiable."""
        manager = TaskManager()
        assert manager is not None


class TestSingleActiveTaskConstraint:
    """Test single active task constraint enforcement."""

    @pytest.mark.asyncio
    async def test_single_active_task_constraint(self) -> None:
        """TaskManager should reject new active tasks when one is already active."""
        manager = TaskManager()
        task1 = MockTask(task_type=TaskType.ACTIVE)
        task2 = MockTask(task_type=TaskType.ACTIVE)

        # First task should register successfully
        await manager.register_task(task1)

        # Second task should be rejected
        with pytest.raises(RuntimeError, match="Cannot register task: another task is already active"):
            await manager.register_task(task2)

    @pytest.mark.asyncio
    async def test_task_registration_after_completion(self) -> None:
        """TaskManager should allow new tasks after completing the active one."""
        manager = TaskManager()
        task1 = MockTask(task_type=TaskType.ACTIVE)
        task2 = MockTask(task_type=TaskType.ACTIVE)

        # Register and complete first task
        await manager.register_task(task1)
        await manager.complete_task(task1)

        # Second task should now register successfully
        await manager.register_task(task2)


class TestScheduledTaskPauseLogic:
    """Test scheduled task pause/resume logic."""

    @pytest.mark.asyncio
    async def test_scheduled_tasks_paused_when_active_task_starts(self) -> None:
        """Scheduled tasks should be paused when active task starts."""
        manager = TaskManager()
        scheduled_task = MockTask(task_type=TaskType.SCHEDULED)
        active_task = MockTask(task_type=TaskType.ACTIVE)

        # Register scheduled task first
        await manager.register_task(scheduled_task)
        assert not scheduled_task.paused

        # Register active task - should pause scheduled task
        await manager.register_task(active_task)
        assert scheduled_task.paused

    @pytest.mark.asyncio
    async def test_scheduled_tasks_resumed_when_active_task_completes(self) -> None:
        """Scheduled tasks should be resumed when active task completes."""
        manager = TaskManager()
        scheduled_task = MockTask(task_type=TaskType.SCHEDULED)
        active_task = MockTask(task_type=TaskType.ACTIVE)

        # Register both tasks
        await manager.register_task(scheduled_task)
        await manager.register_task(active_task)
        assert scheduled_task.paused

        # Complete active task - should resume scheduled task
        await manager.complete_task(active_task)
        # Give a moment for the async resume to complete
        await asyncio.sleep(0.01)
        assert not scheduled_task.paused

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_multiple_scheduled_tasks_coordination(self) -> None:
        """Multiple scheduled tasks should all be paused/resumed together."""
        manager = TaskManager()
        scheduled1 = MockTask(task_type=TaskType.SCHEDULED)
        scheduled2 = MockTask(task_type=TaskType.SCHEDULED)
        active_task = MockTask(task_type=TaskType.ACTIVE)

        # Register scheduled tasks
        await manager.register_task(scheduled1)
        await manager.register_task(scheduled2)
        assert not scheduled1.paused
        assert not scheduled2.paused

        # Register active task - should pause all scheduled tasks
        await manager.register_task(active_task)
        assert scheduled1.paused
        assert scheduled2.paused

        # Complete active task - should resume all scheduled tasks
        await manager.complete_task(active_task)
        await asyncio.sleep(0.01)
        assert not scheduled1.paused
        assert not scheduled2.paused


class TestTaskStateManagement:
    """Test task state management and lifecycle coordination."""

    @pytest.mark.asyncio
    async def test_task_state_transitions_processed(self) -> None:
        """TaskManager should process task state transitions."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Register task - should process ACTIVE state
        await manager.register_task(task)
        assert manager._active_task == task

    @pytest.mark.asyncio
    async def test_task_completion_state_processed(self) -> None:
        """TaskManager should process task completion states."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Mock completed method to return IDLE state
        async def mock_completed() -> tuple[TaskState, str | None]:
            return (TaskState.IDLE, "Task completed")

        task.completed = mock_completed  # type: ignore[method-assign]

        await manager.register_task(task)
        assert manager._active_task == task

        # Handle completion - should process IDLE state and clear active task
        await manager._handle_task_completion(task)
        assert manager._active_task is None
        assert len(manager._pending_instructions) == 1
        assert manager._pending_instructions[0] == "Task completed"

    @pytest.mark.asyncio
    async def test_timeout_state_processed(self) -> None:
        """TaskManager should process timeout state transitions."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Mock timeout_expired to return IDLE state
        async def mock_timeout() -> tuple[TaskState, str | None]:
            return (TaskState.IDLE, "Task timed out")

        task.timeout_expired = mock_timeout  # type: ignore[method-assign]

        await manager.register_task(task)
        assert manager._active_task == task

        # Simulate timeout
        await manager._handle_timeout_for_task(0.001, task)
        assert manager._active_task is None
        assert len(manager._pending_instructions) == 1
        assert manager._pending_instructions[0] == "Task timed out"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_task_response_state_processed(self) -> None:
        """TaskManager should process task response state changes."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Mock response method to return COMPLETED state
        async def mock_response(data: Any) -> tuple[TaskState, str | None]:
            return (TaskState.COMPLETED, "Response processed")

        task.response = mock_response  # type: ignore[method-assign]

        await manager.register_task(task)

        # Handle response - should process COMPLETED state
        await manager.handle_task_response(task, {"test": "data"})
        assert len(manager._pending_instructions) == 1
        assert manager._pending_instructions[0] == "Response processed"


class TestTaskRegistration:
    """Test TaskManager can register tasks."""

    @pytest.mark.asyncio
    async def test_task_manager_can_register_task(self) -> None:
        """TaskManager should be able to register a task."""
        manager = TaskManager()
        task = MockTask()

        await manager.register_task(task)

        # Task should have been started
        assert task.task_start_called


class TestTimeoutHandling:
    """Test TaskManager timeout handling."""

    @pytest.mark.asyncio
    async def test_task_with_timeout_creates_timeout_task(self) -> None:
        """TaskManager should create timeout task for tasks with positive timeout."""
        manager = TaskManager()
        task = MockTask(timeout=1.0)

        # Register task and verify timeout task is created
        await manager.register_task(task)

        # Should have created a timeout task
        assert task in manager._timeout_tasks
        assert manager._timeout_tasks[task] is not None

        # Clean up to avoid warnings
        await manager.complete_task(task)
        assert task not in manager._timeout_tasks

    @pytest.mark.asyncio
    async def test_task_with_zero_timeout_does_not_create_timeout_task(self) -> None:
        """Tasks with zero timeout should not have a timeout task scheduled."""
        manager = TaskManager()
        task = MockTask(timeout=0)

        await manager.register_task(task)

        # Should not have created a timeout task
        assert task not in manager._timeout_tasks
        assert len(manager._timeout_tasks) == 0

    @pytest.mark.asyncio
    async def test_task_with_negative_timeout_does_not_create_timeout_task(self) -> None:
        """Tasks with negative timeout should not have a timeout task scheduled."""
        manager = TaskManager()
        task = MockTask(timeout=-1.0)

        await manager.register_task(task)

        # Should not have created a timeout task
        assert task not in manager._timeout_tasks
        assert len(manager._timeout_tasks) == 0


class TestResultEnhancement:
    """Test Result class has additional_agent_instructions field."""

    def test_result_has_additional_instruction_field(self) -> None:
        """Result should have additional_agent_instructions field for side-band communication."""
        result = Result.ok("test", additional_agent_instructions="Please check file status")

        assert hasattr(result, "additional_agent_instructions")
        assert result.additional_agent_instructions == "Please check file status"

    def test_failure_result_has_additional_instruction_field(self) -> None:
        """Failure Result should also support additional_agent_instructions for side-band communication."""
        result: Result[str] = Result.failure("error", additional_agent_instructions="Check logs")

        assert hasattr(result, "additional_agent_instructions")
        assert result.additional_agent_instructions == "Check logs"
        assert not result.success


class TestAgentDataInterception:
    """Test agent data interception system."""

    @pytest.fixture
    def task_manager(self) -> TaskManager:
        """Create TaskManager instance."""
        return TaskManager()

    @pytest.fixture
    def mock_task(self) -> MockTask:
        """Create mock task."""
        task = MockTask()
        task.process_data = AsyncMock()
        return task

    @pytest.mark.asyncio
    async def test_register_interest(self, task_manager: TaskManager, mock_task: MockTask) -> None:
        """Test interest registration."""
        callback = lambda dt, data: True
        await task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        assert len(task_manager._subscriptions) == 1

    @pytest.mark.asyncio
    async def test_dispatch_event_no_interest(self, task_manager: TaskManager) -> None:
        """Test handling data with no interested tasks."""
        result = await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": "test.txt"})
        assert result == {"status": "acknowledged"}

    @pytest.mark.asyncio
    async def test_dispatch_event_with_interest(self, task_manager: TaskManager, mock_task: MockTask) -> None:
        """Test handling data with interested task."""
        await task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        result = await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": "test.txt", "content": "data"})

        assert result == {"status": "processed"}
        # Check that handle_event was called with the correct data
        assert len(mock_task.received_events) == 1
        event_type, data = mock_task.received_events[0]
        assert event_type == EventType.FS_FILE_CONTENT
        assert data == {"path": "test.txt", "content": "data"}

    @pytest.mark.asyncio
    async def test_bit_flag_filtering(self, task_manager: TaskManager, mock_task: MockTask) -> None:
        """Test bit-flag pre-filtering."""
        callback = lambda dt, data: True  # Always interested
        await task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        # Send different data type - should not call callback
        result = await task_manager.dispatch_event(EventType.FS_DIRECTORY, {"entries": []})

        assert result == {"status": "acknowledged"}
        mock_task.process_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_callback_returns_false_after_bit_flag_match(
        self, task_manager: TaskManager, mock_task: MockTask
    ) -> None:
        """Test that callback returning False prevents processing even when bit-flags match."""
        mock_task.handle_event_return = False  # Never interested
        await task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        result = await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": "test.txt"})

        assert result == {"status": "acknowledged"}
        mock_task.process_data.assert_not_called()
        # Registration should not be expired since no processing occurred
        assert len(task_manager._subscriptions) == 1

    @pytest.mark.asyncio
    async def test_persistent_registration_behavior(self, task_manager: TaskManager, mock_task: MockTask) -> None:
        """Test registration persists after handling."""
        callback = lambda dt, data: True
        await task_manager.subscribe(mock_task, EventType.FS_FILE_CONTENT)

        # Process data
        await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": "test.txt"})

        # Registration should persist
        assert len(task_manager._subscriptions) == 1


class TestResultProcessing:
    """Test Result processing and instruction queuing."""

    @pytest.fixture
    def task_manager(self) -> TaskManager:
        """Create TaskManager instance."""
        return TaskManager()

    @pytest.mark.asyncio
    async def test_queue_instruction(self, task_manager: TaskManager) -> None:
        """Test queuing instructions for next response."""
        await task_manager.queue_instruction("Please check file status")
        assert len(task_manager._pending_instructions) == 1
        assert task_manager._pending_instructions[0] == "Please check file status"

    async def test_process_result_no_instructions(self, task_manager: TaskManager) -> None:
        """Test processing result with no pending instructions."""
        from mcp_core.result import Result

        original_result = Result.ok("test data")

        processed_result = await task_manager.process_result(original_result)

        assert processed_result == original_result
        assert processed_result.additional_agent_instructions is None

    async def test_process_result_with_instruction(self, task_manager: TaskManager) -> None:
        """Test processing result with pending instruction."""
        from mcp_core.result import Result

        original_result = Result.ok("test data")
        await task_manager.queue_instruction("Please check file status")

        processed_result = await task_manager.process_result(original_result)

        assert processed_result.success == original_result.success
        assert processed_result.value == original_result.value
        assert processed_result.additional_agent_instructions == "Please check file status"
        assert len(task_manager._pending_instructions) == 0  # Should be consumed

    async def test_process_result_fifo_order(self, task_manager: TaskManager) -> None:
        """Test instructions are processed in FIFO order."""
        from mcp_core.result import Result

        await task_manager.queue_instruction("First instruction")
        await task_manager.queue_instruction("Second instruction")

        result1 = await task_manager.process_result(Result.ok("data1"))
        result2 = await task_manager.process_result(Result.ok("data2"))

        assert result1.additional_agent_instructions == "First instruction"
        assert result2.additional_agent_instructions == "Second instruction"
        assert len(task_manager._pending_instructions) == 0
