# Instruction Retry with Acknowledgement

## Why

Tasks queue instructions to the agent but have no feedback mechanism. If the agent ignores an instruction, the task becomes blocked indefinitely waiting for data that never arrives. There is no way to:

- Detect if an instruction was ignored
- Retry failed instructions
- Distinguish between "not yet executed" vs "permanently ignored"
- Debug instruction delivery issues

This creates reliability problems where tasks silently fail when agents don't cooperate.

## What Changes

Add an acknowledgement-based instruction tracking system with automatic retry:

- New `queue_instruction_with_ack()` method returns tracking ID
- New `acknowledge_instruction()` method to confirm receipt
- New `RetryTask` monitors idle periods and requeues unacknowledged instructions
- Retry counter escalates instruction urgency with **IMPORTANT** prefix
- Deduplication prevents same instruction being queued multiple times
- Existing `queue_instruction()` unchanged for backward compatibility

## Impact

- Affected specs: `refactor-task-pubsub` (MODIFIED - add instruction tracking requirements)
- Affected code:
  - `src/mcp_guide/task_manager.py` - Add tracking methods and data structures
  - `src/mcp_guide/tasks/` - New `RetryTask` for monitoring
  - `src/mcp_guide/openspec/task.py` - Migrate to use acknowledgement
  - `src/mcp_guide/context/tasks.py` - Migrate to use acknowledgement
  - `src/mcp_guide/workflow/tasks.py` - Migrate to use acknowledgement
- Breaking changes: None (new API, existing code unchanged)

## Design

### Retry Mechanism

**RetryTask** runs on 60-second timer and checks for unacknowledged instructions:

1. Check if instruction queue is empty (idle state)
2. If not empty, skip (MCP is active or results pending dispatch)
3. If empty, check for tracked instructions awaiting acknowledgement
4. Requeue unacknowledged instructions with escalating urgency prefix

**Urgency Escalation:**
- 1st retry: No prefix
- 2nd retry: Prefix with "**IMPORTANT:** "
- 3rd+ retry: Prefix with "**URGENT:** "

### New API

```python
# Task queues instruction with acknowledgement tracking
instruction_id = await task_manager.queue_instruction_with_ack(
    content="Check for OpenSpec CLI",
    max_retries=3
)

# Task stores ID locally
self._pending_instruction_id = instruction_id

# Later, when task receives the expected response
async def handle_event(self, event_type, data):
    if self._is_expected_response(event_type, data):
        # Acknowledge receipt - prevents retry
        await self.task_manager.acknowledge_instruction(self._pending_instruction_id)
        self._pending_instruction_id = None
```

### Deduplication

If the same instruction content is queued while already tracked:
- Return existing instruction ID
- Do not add duplicate to queue
- Prevents instruction "doubling up"

### Internal Tracking

```python
@dataclass
class TrackedInstruction:
    id: str                    # UUID for tracking
    content: str               # Original instruction text
    queued_at: float          # First queue timestamp
    retry_count: int = 0      # Number of times requeued
    max_retries: int = 3      # Give up after this many retries
```

TaskManager maintains:
- `_pending_instructions: List[str]` - Existing queue (unchanged)
- `_tracked_instructions: Dict[str, TrackedInstruction]` - Instructions awaiting acknowledgement
- `_content_to_id: Dict[str, str]` - Content hash to ID for deduplication

### RetryTask Logic

```python
class RetryTask(Task):
    """Monitor and retry unacknowledged instructions."""

    async def handle_event(self, event_type: EventType, data: dict) -> None:
        if not (event_type & EventType.TIMER):
            return

        # Only retry when queue is idle
        if not self.task_manager.is_queue_empty():
            return

        # Requeue unacknowledged instructions
        await self.task_manager.retry_unacknowledged()
```

### TaskManager Methods

```python
async def queue_instruction_with_ack(
    self,
    content: str,
    max_retries: int = 3
) -> str:
    """Queue instruction with acknowledgement tracking.

    Returns:
        Instruction ID for acknowledgement
    """
    # Check for duplicate
    if content in self._content_to_id:
        return self._content_to_id[content]

    # Create tracked instruction
    instr_id = str(uuid.uuid4())
    tracked = TrackedInstruction(
        id=instr_id,
        content=content,
        queued_at=time.time(),
        max_retries=max_retries
    )

    self._tracked_instructions[instr_id] = tracked
    self._content_to_id[content] = instr_id
    self._pending_instructions.append(content)

    return instr_id

async def acknowledge_instruction(self, instruction_id: str) -> None:
    """Acknowledge instruction receipt - prevents retry."""
    if instruction_id in self._tracked_instructions:
        tracked = self._tracked_instructions[instruction_id]
        del self._tracked_instructions[instruction_id]
        del self._content_to_id[tracked.content]

async def retry_unacknowledged(self) -> None:
    """Requeue unacknowledged instructions with urgency prefix."""
    for instr_id, tracked in list(self._tracked_instructions.items()):
        if tracked.retry_count >= tracked.max_retries:
            # Give up
            logger.warning(
                f"Instruction {instr_id} failed after {tracked.max_retries} retries: "
                f"{tracked.content[:50]}..."
            )
            del self._tracked_instructions[instr_id]
            del self._content_to_id[tracked.content]
        else:
            # Requeue with urgency prefix
            tracked.retry_count += 1

            if tracked.retry_count == 1:
                content = tracked.content
            elif tracked.retry_count == 2:
                content = f"**IMPORTANT:** {tracked.content}"
            else:
                content = f"**URGENT:** {tracked.content}"

            self._pending_instructions.append(content)
```

### Task Correlation

Tasks correlate responses by **event content/type**, not by ID propagation:

```python
class OpenSpecTask:
    async def request_cli_check(self):
        content = await render_template("openspec-cli-check")
        self._cli_check_id = await self.task_manager.queue_instruction_with_ack(
            content,
            max_retries=3
        )

    async def handle_event(self, event_type, data):
        if event_type & EventType.FS_COMMAND:
            if data.get("command") == "openspec":
                # This is the CLI check response
                if self._cli_check_id:
                    await self.task_manager.acknowledge(self._cli_check_id)
                    self._cli_check_id = None

                # Process the response
                self._available = data.get("found", False)
```

## Benefits

1. **Reliability** - Instructions are retried automatically
2. **Observability** - Can see which instructions failed
3. **No agent changes** - Agent protocol unchanged
4. **Backward compatible** - Existing `queue_instruction()` works as before
5. **Simple** - No timeouts, no complex state machines
6. **Deterministic** - Max retries is clear and predictable

## Non-Goals

- Timeout-based retry (use max retries instead)
- Status query API (TaskManager handles internally)
- ID propagation to agent (internal only)
- Guaranteed delivery (agent cooperation still required)

## Implementation Notes

### Idempotency Required

Instructions must be idempotent since they may be sent multiple times:

```python
# Good: Idempotent
"Check if OpenSpec CLI is available"
"List contents of openspec/ directory"

# Bad: Not idempotent
"Create new file"
"Increment counter"
```

### Retry Limits

Default `max_retries=3` means:
- 1st attempt: Initial dispatch
- 2nd attempt: First retry
- 3rd attempt: Second retry
- 4th attempt: Final retry
- After 4th: Give up, move to failed

### Failed Instruction Handling

Failed instructions are logged and stored for debugging:

```python
# Can query failed instructions
failed = task_manager.get_failed_instructions()
for instr_id, instr in failed.items():
    logger.error(f"Failed: {instr.content} (retries: {instr.retry_count})")
```

## Migration Path

1. **Phase 1**: Add new API, no behavior changes
   - `queue_instruction_with_ack()` available
   - Existing code unchanged

2. **Phase 2**: Migrate critical tasks
   - OpenSpecTask uses ACK for CLI/project checks
   - ClientContextTask uses ACK for OS info

3. **Phase 3**: Add observability
   - Dashboard shows sent/failed instructions
   - Metrics for retry rates

## Alternatives Considered

### 1. Timeout-based retry
**Rejected**: Complex time management, clock sync issues, non-deterministic

### 2. Status query API
**Rejected**: Adds complexity, tasks must poll, TaskManager should handle internally

### 3. ID propagation to agent
**Rejected**: Requires agent protocol changes, breaks existing agents

### 4. Guaranteed delivery
**Rejected**: Impossible without agent cooperation, better to fail explicitly

## Success Criteria

- Tasks can queue instructions with acknowledgement
- Unacknowledged instructions are retried up to max_retries
- Failed instructions are logged and observable
- Existing `queue_instruction()` behavior unchanged
- No agent protocol changes required
- OpenSpecTask and ClientContextTask successfully use new API
