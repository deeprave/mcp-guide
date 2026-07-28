## Context

Rendered guidance depends on the client's command and storage capabilities. The current detection table treats Cursor as prompt-capable and omits Aider, which makes the output misleading.

## Goals / Non-Goals

**Goals:**
- Explicitly represent prompt support and Aider recognition.
- Keep agent-dependent output and knowledge destinations coherent.

**Non-Goals:**
- Adding integrations for agents without a documented project-local convention.

## Decisions

- Model unsupported prompt invocation with `None`, not a placeholder prefix.
- Add Aider as an explicit canonical agent and audit mappings as a single capability table.

## Risks / Trade-offs

- [Client naming varies] → use narrowly scoped aliases with unit tests.
- [Undocumented integrations change] → preserve unknown-agent fallback behavior.
