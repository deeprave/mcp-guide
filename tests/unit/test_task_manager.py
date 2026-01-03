"""Tests for TaskManager core infrastructure."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from mcp_core.result import Result
from mcp_guide.task_manager import DataType, TaskManager, TaskState, TaskType


class MockTask:
    """Mock task for testing."""

    def __init__(self, timeout: float | None = None, task_type: TaskType = TaskType.ACTIVE):
        self.timeout = timeout
        self.task_type = task_type
        self.task_start_called = False
        self.timeout_expired_called = False
        self.paused = False

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

    async def response(self, data: any) -> tuple[TaskState, str | None]:
        """Handle response data."""
        return (TaskState.COMPLETED, None)

    async def timeout_expired(self) -> tuple[TaskState, str | None]:
        """Handle timeout expiry."""
        self.timeout_expired_called = True
        return (TaskState.IDLE, None)

    async def completed(self) -> tuple[TaskState, str | None]:
        """Handle task completion."""
        return (TaskState.IDLE, None)

    async def process_data(self, data_type: DataType, data: dict) -> None:
        """Process agent data."""
        pass


class TestTaskManagerInstantiation:
    """Test TaskManager can be created."""

    def test_task_manager_can_be_instantiated(self):
        """TaskManager should be instantiable."""
        manager = TaskManager()
        assert manager is not None


class TestSingleActiveTaskConstraint:
    """Test single active task constraint enforcement."""

    async def test_single_active_task_constraint(self):
        """TaskManager should reject new active tasks when one is already active."""
        manager = TaskManager()
        task1 = MockTask(task_type=TaskType.ACTIVE)
        task2 = MockTask(task_type=TaskType.ACTIVE)

        # First task should register successfully
        await manager.register_task(task1)

        # Second task should be rejected
        with pytest.raises(RuntimeError, match="Cannot register task: another task is already active"):
            await manager.register_task(task2)

    async def test_task_registration_after_completion(self):
        """TaskManager should allow new tasks after completing the active one."""
        manager = TaskManager()
        task1 = MockTask(task_type=TaskType.ACTIVE)
        task2 = MockTask(task_type=TaskType.ACTIVE)

        # Register and complete first task
        await manager.register_task(task1)
        manager.complete_task(task1)

        # Second task should now register successfully
        await manager.register_task(task2)


class TestScheduledTaskPauseLogic:
    """Test scheduled task pause/resume logic."""

    async def test_scheduled_tasks_paused_when_active_task_starts(self):
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

    async def test_scheduled_tasks_resumed_when_active_task_completes(self):
        """Scheduled tasks should be resumed when active task completes."""
        manager = TaskManager()
        scheduled_task = MockTask(task_type=TaskType.SCHEDULED)
        active_task = MockTask(task_type=TaskType.ACTIVE)

        # Register both tasks
        await manager.register_task(scheduled_task)
        await manager.register_task(active_task)
        assert scheduled_task.paused

        # Complete active task - should resume scheduled task
        manager.complete_task(active_task)
        # Give a moment for the async resume to complete
        await asyncio.sleep(0.01)
        assert not scheduled_task.paused

    async def test_multiple_scheduled_tasks_coordination(self):
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
        manager.complete_task(active_task)
        await asyncio.sleep(0.01)
        assert not scheduled1.paused
        assert not scheduled2.paused


class TestTaskStateManagement:
    """Test task state management and lifecycle coordination."""

    async def test_task_state_transitions_processed(self):
        """TaskManager should process task state transitions."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Register task - should process ACTIVE state
        await manager.register_task(task)
        assert manager._active_task == task

    async def test_task_completion_state_processed(self):
        """TaskManager should process task completion states."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Mock completed method to return IDLE state
        async def mock_completed():
            return (TaskState.IDLE, "Task completed")

        task.completed = mock_completed

        await manager.register_task(task)
        assert manager._active_task == task

        # Handle completion - should process IDLE state and clear active task
        await manager._handle_task_completion(task)
        assert manager._active_task is None
        assert len(manager._pending_instructions) == 1
        assert manager._pending_instructions[0] == "Task completed"

    async def test_timeout_state_processed(self):
        """TaskManager should process timeout state transitions."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Mock timeout_expired to return IDLE state
        async def mock_timeout():
            return (TaskState.IDLE, "Task timed out")

        task.timeout_expired = mock_timeout

        await manager.register_task(task)
        assert manager._active_task == task

        # Simulate timeout
        await manager._handle_timeout_for_task(0.001, task)
        assert manager._active_task is None
        assert len(manager._pending_instructions) == 1
        assert manager._pending_instructions[0] == "Task timed out"

    async def test_task_response_state_processed(self):
        """TaskManager should process task response state changes."""
        manager = TaskManager()
        task = MockTask(task_type=TaskType.ACTIVE)

        # Mock response method to return COMPLETED state
        async def mock_response(data):
            return (TaskState.COMPLETED, "Response processed")

        task.response = mock_response

        await manager.register_task(task)

        # Handle response - should process COMPLETED state
        await manager.handle_task_response(task, {"test": "data"})
        assert len(manager._pending_instructions) == 1
        assert manager._pending_instructions[0] == "Response processed"


class TestTaskRegistration:
    """Test TaskManager can register tasks."""

    @pytest.mark.asyncio
    async def test_task_manager_can_register_task(self):
        """TaskManager should be able to register a task."""
        manager = TaskManager()
        task = MockTask()

        await manager.register_task(task)

        # Task should have been started
        assert task.task_start_called


class TestTimeoutHandling:
    """Test TaskManager timeout handling."""

    @pytest.mark.asyncio
    async def test_task_with_timeout_creates_timeout_task(self):
        """TaskManager should create timeout task for tasks with timeout."""
        manager = TaskManager()
        task = MockTask(timeout=1.0)

        # Register task and verify timeout task is created
        await manager.register_task(task)

        # Should have created a timeout task
        assert task in manager._timeout_tasks
        assert manager._timeout_tasks[task] is not None

        # Clean up to avoid warnings
        manager.complete_task(task)
        assert task not in manager._timeout_tasks


class TestResultEnhancement:
    """Test Result class has additional_instruction field."""

    def test_result_has_additional_instruction_field(self):
        """Result should have additional_instruction field for side-band communication."""
        result = Result.ok("test", additional_instruction="Please check file status")

        assert hasattr(result, "additional_instruction")
        assert result.additional_instruction == "Please check file status"


class TestAgentDataInterception:
    """Test agent data interception system."""

    @pytest.fixture
    def task_manager(self):
        """Create TaskManager instance."""
        return TaskManager()

    @pytest.fixture
    def mock_task(self):
        """Create mock task."""
        task = MockTask()
        task.process_data = AsyncMock()
        return task

    def test_register_interest(self, task_manager, mock_task):
        """Test interest registration."""
        callback = lambda dt, data: True
        task_manager.register_interest(mock_task, DataType.FILE_CONTENT, callback)

        assert len(task_manager._registrations) == 1
        assert task_manager._registrations[0].task == mock_task
        assert task_manager._registrations[0].flags == DataType.FILE_CONTENT

    async def test_handle_agent_data_no_interest(self, task_manager):
        """Test handling data with no interested tasks."""
        result = await task_manager.handle_agent_data(DataType.FILE_CONTENT, {"path": "test.txt"})
        assert result == {"status": "acknowledged"}

    async def test_handle_agent_data_with_interest(self, task_manager, mock_task):
        """Test handling data with interested task."""
        callback = lambda dt, data: data.get("path") == "test.txt"
        task_manager.register_interest(mock_task, DataType.FILE_CONTENT, callback)

        result = await task_manager.handle_agent_data(DataType.FILE_CONTENT, {"path": "test.txt", "content": "data"})

        assert result == {"status": "processed"}
        mock_task.process_data.assert_called_once_with(DataType.FILE_CONTENT, {"path": "test.txt", "content": "data"})

    async def test_bit_flag_filtering(self, task_manager, mock_task):
        """Test bit-flag pre-filtering."""
        callback = lambda dt, data: True  # Always interested
        task_manager.register_interest(mock_task, DataType.FILE_CONTENT, callback)

        # Send different data type - should not call callback
        result = await task_manager.handle_agent_data(DataType.DIRECTORY_LISTING, {"entries": []})

        assert result == {"status": "acknowledged"}
        mock_task.process_data.assert_not_called()

    async def test_ephemeral_registration_expiry(self, task_manager, mock_task):
        """Test registration expires after handling."""
        callback = lambda dt, data: True
        task_manager.register_interest(mock_task, DataType.FILE_CONTENT, callback)

        # Process data
        await task_manager.handle_agent_data(DataType.FILE_CONTENT, {"path": "test.txt"})

        # Registration should be expired
        assert len(task_manager._registrations) == 0


class TestResultProcessing:
    """Test Result processing and instruction queuing."""

    @pytest.fixture
    def task_manager(self):
        """Create TaskManager instance."""
        return TaskManager()

    def test_queue_instruction(self, task_manager):
        """Test queuing instructions for next response."""
        task_manager.queue_instruction("Please check file status")
        assert len(task_manager._pending_instructions) == 1
        assert task_manager._pending_instructions[0] == "Please check file status"

    def test_process_result_no_instructions(self, task_manager):
        """Test processing result with no pending instructions."""
        from mcp_core.result import Result

        original_result = Result.ok("test data")

        processed_result = task_manager.process_result(original_result)

        assert processed_result == original_result
        assert processed_result.additional_instruction is None

    def test_process_result_with_instruction(self, task_manager):
        """Test processing result with pending instruction."""
        from mcp_core.result import Result

        original_result = Result.ok("test data")
        task_manager.queue_instruction("Please check file status")

        processed_result = task_manager.process_result(original_result)

        assert processed_result.success == original_result.success
        assert processed_result.value == original_result.value
        assert processed_result.additional_instruction == "Please check file status"
        assert len(task_manager._pending_instructions) == 0  # Should be consumed

    def test_process_result_fifo_order(self, task_manager):
        """Test instructions are processed in FIFO order."""
        from mcp_core.result import Result

        task_manager.queue_instruction("First instruction")
        task_manager.queue_instruction("Second instruction")

        result1 = task_manager.process_result(Result.ok("data1"))
        result2 = task_manager.process_result(Result.ok("data2"))

        assert result1.additional_instruction == "First instruction"
        assert result2.additional_instruction == "Second instruction"
        assert len(task_manager._pending_instructions) == 0
