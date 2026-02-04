# Implementation Tasks

## 1. Add Startup Decorator Infrastructure

- [x] 1.1 Add `_startup_handlers` list to GuideMCP class
- [x] 1.2 Implement `on_init()` decorator method in GuideMCP
- [x] 1.3 Create `guide_lifespan()` async context manager in server.py
- [x] 1.4 Wire lifespan to GuideMCP initialization in `create_server()`

## 2. Update Task Protocol

- [x] 2.1 Add `on_init()` method to TaskSubscriber protocol
- [x] 2.2 Document that `on_init()` is called once at server startup

## 3. Update Task Manager

- [x] 3.1 Add `session` and `resolved_flags` properties to TaskManager
- [x] 3.2 Implement `on_init()` method in TaskManager:
  - Establish session using `get_or_create_session()`
  - Load and cache resolved flags
  - Call `on_init()` on all registered tasks
- [x] 3.3 Expose session and flags to tasks via properties
- [x] 3.4 Add `requires_flag()` helper method for common flag checking pattern

## 4. Register Task Manager Initialization

- [x] 4.1 Create startup handler that calls `task_manager.on_init()`
- [x] 4.2 Register handler using `@guide.on_init()` decorator

## 5. Update Tasks

- [x] 5.1 Implement `on_init()` in OpenSpecTask
- [x] 5.2 Implement `on_init()` in WorkflowMonitorTask
- [x] 5.3 Implement `on_init()` in ClientContextTask
- [x] 5.4 Update all tasks to use `requires_flag()` helper

## 6. Testing

- [x] 6.1 Add unit tests for `@guide.on_init()` decorator
- [x] 6.2 Add unit tests for TaskManager.on_init()
- [x] 6.3 Add unit tests for lifespan execution
- [x] 6.4 Add unit tests for task on_init() implementations
- [x] 6.5 Add unit tests for `requires_flag()` helper
- [x] 6.6 Verify all existing tests pass (1277 tests passing)

## 7. Quality Checks

- [x] 7.1 All tests pass with no warnings
- [x] 7.2 Ruff linting passes
- [x] 7.3 MyPy type checking passes
- [x] 7.4 Code formatting applied

## Summary

**Completed:**
- ✅ Full server initialization infrastructure with `@guide.on_init()` decorator
- ✅ TaskManager centralized initialization with session and flags
- ✅ All three tasks (OpenSpecTask, WorkflowMonitorTask, ClientContextTask) updated
- ✅ Added `requires_flag()` helper method for cleaner flag checking
- ✅ Comprehensive test coverage (14 new tests, all passing)
- ✅ All quality checks passing (tests, lint, types, format)

**What remains:**
- Nothing - implementation is complete

**Notes:**
- TIMER_ONCE event type remains available for other use cases
- Only removed initialization workarounds, not the event type itself
- Added bonus `requires_flag()` helper for common pattern
- All 1277 tests passing
