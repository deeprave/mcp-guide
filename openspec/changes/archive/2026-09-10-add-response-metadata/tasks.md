## 1. Protocol identity

- [x] 1.1 Add an immutable Session protocol type derived from the negotiated revision, preserving the exact revision for logging and rejecting a type mismatch for a retained Session; verify legacy and `2026-07-28` session-establishment behaviour.

## 2. Protocol-specific response delivery

- [x] 2.1 Add failing adapter tests for the preserved legacy structured `additional_agent_instructions` field and for the `2026-07-28` `_meta["mcp-guide"]["instructions"]` scalar value without structured-payload duplication.
- [x] 2.2 Adapt tool, prompt, and resource responses from the resolved Session protocol type, preserving Result and TaskManager behaviour; verify all three public surfaces in both protocol modes.

## 3. Contract and verification

- [x] 3.1 Document the modern metadata path, the unchanged legacy field, scalar FIFO delivery, and the Session protocol-type boundary; verify the documentation renders with `mkdocs build --strict`.
- [x] 3.2 Run focused session, TaskManager, response-adapter, and public-surface pytest suites in a foreground PTY, then run `ruff check .` and `openspec validate add-response-metadata --strict --no-interactive`; verify all commands pass.
