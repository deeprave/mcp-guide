## Context

See [proposal.md](proposal.md) for the motivation.  The TaskManager currently pops the oldest queued instruction, uses `dataclasses.replace()` to insert it into `Result.additional_agent_instructions`, and sends the resulting payload through every response adapter.  This incorrectly presents an asynchronously queued session event as a property of the handler's result.

`ResponseMetadata` is already the SDK-neutral boundary for values that travel beside a response.  The existing adapters can attach metadata to native tool, prompt, and resource responses, but current dispatch helpers only return a processed Result rather than a result-and-metadata pair.

## Goals / Non-Goals

**Goals:**

- Preserve strict separation between the handler result and session-generated side-band delivery.
- Trial FIFO-ordered list delivery for all pending side-band instructions.
- Provide one consistent metadata contract on tools, prompts, and resources.

**Non-Goals:**

- Assigning priority or urgency semantics to queue order.
- Changing the acknowledgement or retry behaviour of tracked instructions.
- Defining cache metadata or changing the standard MCP protocol.

## Decisions

### Use a response envelope internally

Introduce an SDK-neutral response envelope containing the original `Result` and optional `ResponseMetadata`.  TaskManager response processing returns this envelope instead of mutating or replacing the result.  Dispatch helpers pass its two components to the existing native adapters.

Alternative considered: add side-band fields to `Result` but omit them from `to_json()`.  That retains the misleading data model and makes it easy for internal code to couple result correctness to a queued event.

### Trial a FIFO-ordered instruction list

`ResponseMetadata.additional_agent_instructions` becomes an optional list of strings.  On each outgoing response the TaskManager removes the current pending queue in FIFO order and assigns that list to the field.  The list is a trial: its ordering records enqueue/delivery sequence only and SHALL NOT imply priority or required action order.

Alternative considered: retain one scalar instruction per response.  It avoids the risk that agents action only the first item or infer priority, but delays all later pending work until unrelated future responses.  This change deliberately trials list delivery so that real agent handling can determine whether that trade-off is acceptable; it can be reverted if list handling proves unreliable.

### Use a Guide-namespaced metadata value

The native adapter writes the queued instruction list to `_meta["mcp-guide/additional_agent_instructions"]`.  It is an application extension rather than an MCP protocol command.  No empty key is emitted.  `Result.to_json()` and the `guide_result` copy contain only result-specific information.

Alternative considered: place the value in user-visible text or structured content.  That would again make unrelated session work appear to be part of the handler response and can alter how clients render actual content.

### Keep result-specific guidance on Result

`instruction` and `disposition` remain part of `Result`; they explain how to use or present the accompanying content.  The migration removes only `additional_agent_instructions` from the Result data model and constructors.

## Risks / Trade-offs

- [Clients only inspect structured Guide results] → Update documented response handling and regression coverage to require inspection of Guide `_meta` instructions.
- [Agents may action only the first list item or infer priority from order] → Document that order is delivery sequence only, add consumer-facing examples, and revert to scalar delivery in a later change if observation shows unreliable handling.
- [A metadata-less direct unit call loses queued delivery] → Keep direct-call behaviour explicit; only paths with a session TaskManager can dequeue session work.
- [A pending instruction is lost after metadata attachment but before client receipt] → Preserve existing dequeue timing and acknowledgement/retry semantics; this change does not claim stronger delivery guarantees.

## Migration Plan

1. Create the response envelope and list-valued metadata field with focused tests.
2. Move TaskManager dequeueing into envelope construction and remove Result mutation.
3. Update all public response dispatch paths and adapters.
4. Remove the Result field and update consumer, surface, and regression tests.
5. Document the metadata key and the breaking move from result payload to `_meta`.
