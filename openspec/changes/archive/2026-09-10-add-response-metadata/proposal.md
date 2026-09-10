## Why

Modern MCP clients need a standard side-band channel for task-generated agent instructions.  Existing clients already consume `Result.additional_agent_instructions`; replacing that field for every protocol would be an unnecessary breaking change.

## What Changes

- Retain the existing scalar, FIFO `Result.additional_agent_instructions` delivery for legacy protocol sessions.
- For a session negotiated with MCP `2026-07-28`, move that instruction to `_meta["mcp-guide"]["instructions"]` and omit it from the structured Guide result.
- Mark each established Session with its immutable protocol type so response adaptation need not repeat transport-version checks.
- Apply the protocol-specific contract consistently to tool, prompt, and resource responses.

## Capabilities

### New Capabilities
- `response-metadata`: Defines the modern Guide side-band instruction metadata contract while preserving legacy structured results.

### Modified Capabilities
- `mcp-v2-request-context`: Records the protocol type on each established Session.
- `tool-infrastructure`: Adapts queued instructions according to the Session protocol type through every public response surface.

## Impact

- Affects Session establishment, result adapters, response dispatch helpers, documentation, and tool/prompt/resource response tests.
- This is additive for MCP `2026-07-28` and preserves legacy response payloads unchanged.
- Does not implement cache policy or cache settings.
