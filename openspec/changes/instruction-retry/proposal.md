# Instruction Retry with Acknowledgement

## Problem

Tasks queue instructions to the agent but have no feedback mechanism. If the agent ignores an instruction, the task becomes blocked indefinitely waiting for data that never arrives. There is no way to:

- Detect if an instruction was ignored
- Retry failed instructions
- Distinguish between "not yet executed" vs "permanently ignored"
- Debug instruction delivery issues

This creates reliability problems where tasks silently fail when agents don't cooperate.

## Solution

Add an acknowledgement-based instruction tracking system that allows tasks to:

1. Queue instructions with tracking enabled
2. Receive confirmation when the agent responds
3. Automatically retry unacknowledged instructions
4. Give up after max retries and log failures

**Key principle:** The instruction ID is internal between Task and TaskManager only. The agent sees plain instructions with no protocol changes required.

## Design

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
        # Acknowledge receipt
        await self.task_manager.acknowledge(self._pending_instruction_id)
        self._pending_instruction_id = None
```

### Internal Tracking

```python
@dataclass
class SentInstruction:
    id: str                    # UUID for tracking
    content: str               # Instruction text
    sent_at: float            # Timestamp (for observability)
    retry_count: int = 0      # Current retry attempt
    max_retries: int = 3      # Give up after this many attempts
```

TaskManager maintains:
- `_pending_instructions: List[str]` - Existing queue (unchanged)
- `_sent_instructions: Dict[str, SentInstruction]` - New tracking queue
- `_failed_instructions: Dict[str, SentInstruction]` - Failed after max retries

### Dispatch Logic

```python
async def _dispatch_instructions(self):
    """Dispatch pending instructions to agent."""

    # First, dispatch new instructions
    while self._pending_instructions:
        content = self._pending_instructions.pop(0)

        # Check if this has tracking enabled
        if content in self._tracked_instructions:
            instr = self._tracked_instructions[content]
            self._sent_instructions[instr.id] = instr
            del self._tracked_instructions[content]

        await self._send_to_agent(content)

    # Then, retry unacknowledged instructions
    for instr_id, instr in list(self._sent_instructions.items()):
        if instr.retry_count >= instr.max_retries:
            # Give up
            self._failed_instructions[instr_id] = instr
            del self._sent_instructions[instr_id]
            logger.warning(f"Instruction {instr_id} failed after {instr.max_retries} retries")
        else:
            # Retry
            instr.retry_count += 1
            await self._send_to_agent(instr.content)
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
