## Context

Rendered guidance depends on the client's command and storage capabilities. The current detection table treats Cursor as prompt-capable and omits Pi, which makes the output misleading.

## Goals / Non-Goals

**Goals:**
- Explicitly represent prompt support and recognise Pi.
- Keep agent-dependent output and knowledge destinations coherent.

**Non-Goals:**
- Updating Aider support until its model-selection behaviour is confirmed.

## Decisions

- Model unsupported prompt invocation with `None`, and make that the default for unrecognised clients; add explicit prefixes only for verified prompt-capable clients.
- Add Pi as an explicit canonical agent and audit mappings as a single capability table.
- Treat `pi-mcp-guide` as a Pi client alias, not as its own agent family.

## Risks / Trade-offs

- [Client naming varies] → use narrowly scoped aliases with unit tests.
- [Undocumented integrations change] → preserve unknown-agent fallback behavior.
