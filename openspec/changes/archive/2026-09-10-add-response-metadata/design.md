## Context

See [proposal.md](proposal.md) for the motivation.  The TaskManager already pops one queued instruction in FIFO order and attaches it to `Result.additional_agent_instructions`.  That established behaviour remains the compatibility contract for retained protocol clients.

## Goals / Non-Goals

**Goals:**

- Preserve the legacy scalar instruction contract without changing TaskManager or Result semantics.
- Provide the standard `_meta` representation for MCP `2026-07-28` clients.
- Provide one consistent protocol-specific contract on tools, prompts, and resources.

**Non-Goals:**

- Changing queue, acknowledgement, retry, or ordering behaviour.
- Defining cache metadata or changing the MCP protocol.

## Decisions

### Record protocol type on the Session

At first request resolution, classify the negotiated revision as `legacy` or `mcp_2026_07_28` and store that immutable type on the Session.  A later request that resolves the same Session under a different type is rejected.  The exact negotiated revision remains available for establishment logging.

### Adapt instructions only for modern Sessions

TaskManager continues to produce the existing scalar `Result.additional_agent_instructions`.  The common response adapter branches on the resolved Session protocol type.  Legacy responses serialise the Result unchanged.  For `mcp_2026_07_28`, the adapter copies the scalar value to `_meta["mcp-guide"]["instructions"]` and serialises a payload without `additional_agent_instructions`.  No empty metadata namespace or key is emitted.

Alternative considered: remove the Result field and re-add it only for legacy serialisation.  That creates a needless new envelope and changes established task behaviour solely to reconstruct it later.

## Risks / Trade-offs

- [Modern clients only inspect structured Guide results] → Document the `_meta` location and add integration coverage for the negotiated modern protocol.
- [Protocol type mismatch] → Reject it rather than silently changing a Session's response contract.
- [A pending instruction is lost after dispatch but before client receipt] → Preserve existing dequeue timing and acknowledgement/retry semantics; this change does not claim stronger delivery guarantees.

## Migration Plan

1. Add an immutable Session protocol type at request establishment.
2. Add modern-protocol response adaptation without changing Result or TaskManager queueing.
3. Cover legacy and modern tool, prompt, and resource response contracts.
4. Document the `_meta` key and preserved legacy field.
