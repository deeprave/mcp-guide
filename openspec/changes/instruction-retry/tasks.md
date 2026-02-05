# Implementation Tasks

## 1. Core Infrastructure

- [x] 1.1 Add `TrackedInstruction` dataclass to task_manager.py
- [x] 1.2 Add tracking dictionaries to TaskManager (`_tracked_instructions`, ~~`_content_to_id`~~)
- [x] 1.3 Implement `queue_instruction_with_ack()` method with deduplication
- [x] 1.4 Implement `acknowledge_instruction()` method
- [x] 1.5 Implement `retry_unacknowledged()` method with urgency escalation
- [x] 1.6 Add `is_queue_empty()` helper method

## 2. RetryTask Implementation

- [x] 2.1 Create `src/mcp_guide/tasks/retry_task.py`
- [x] 2.2 Implement RetryTask with 60-second timer
- [x] 2.3 Add idle detection logic
- [x] 2.4 Register RetryTask with TaskManager on initialization
- [x] 2.5 Add `@task_init` decorator for automatic registration

## 3. OpenSpecTask Migration

- [x] 3.1 Migrate CLI check to use `queue_instruction_with_ack()`
- [x] 3.2 Add acknowledgement in `handle_event()` for CLI response
- [x] 3.3 Migrate project check to use `queue_instruction_with_ack()`
- [x] 3.4 Add acknowledgement in `handle_event()` for project response
- [x] 3.5 Migrate version check to use `queue_instruction_with_ack()`
- [x] 3.6 Add acknowledgement in `handle_event()` for version response
- [x] 3.7 Migrate changes list to use `queue_instruction_with_ack()`
- [x] 3.8 Add acknowledgement in `handle_event()` for changes response

## 4. ClientContextTask Migration

- [x] 4.1 Migrate OS detection to use `queue_instruction_with_ack()`
- [x] 4.2 Add acknowledgement in `handle_event()` for OS response
- [x] 4.3 Migrate working directory to use `queue_instruction_with_ack()`
- [x] 4.4 Add acknowledgement in `handle_event()` for directory response

## 5. WorkflowMonitorTask Migration

- [x] 5.1 Migrate workflow file check to use `queue_instruction_with_ack()`
- [x] 5.2 Add acknowledgement in `handle_event()` for workflow response

## 6. Testing

- [x] 6.1 Unit tests for `queue_instruction_with_ack()` deduplication
- [x] 6.2 Unit tests for `acknowledge_instruction()` cleanup
- [x] 6.3 Unit tests for `retry_unacknowledged()` urgency escalation
- [x] 6.4 Unit tests for max_retries behavior
- [x] 6.5 Integration tests for RetryTask idle detection
- [x] 6.6 Integration tests for end-to-end retry flow

## 7. Documentation

- [x] 7.1 Update TaskManager docstrings
- [x] 7.2 Add migration guide for tasks
- [x] 7.3 Document idempotency requirements
- [x] 7.4 Add examples to task implementation guide
