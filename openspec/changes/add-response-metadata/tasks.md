## 1. Response envelope and result boundary

- [ ] 1.1 Add an SDK-neutral response envelope and list-valued `ResponseMetadata.additional_agent_instructions`, and remove `additional_agent_instructions` from the Result model, constructors, and JSON serialisation; verify Result unit tests distinguish result-specific instruction from side-band metadata.
- [ ] 1.2 Refactor TaskManager result processing to return the original Result plus optional response metadata, dequeueing all pending instructions in FIFO sequence without mutating the Result; verify FIFO, success, failure, empty-queue, and multiple-queued-instruction tests.

## 2. Public response delivery

- [ ] 2.1 Update tool and prompt dispatch helpers to pass the processed response envelope to the native adapters; verify each surface emits side-band metadata without adding it to structured Guide content.
- [ ] 2.2 Update native guide resource processing to propagate the processed response envelope; verify resource metadata independently of its result payload.
- [ ] 2.3 Extend the common adapters to write `mcp-guide/additional_agent_instructions` only for a non-empty list metadata value and preserve unrelated metadata; verify tool, prompt, and resource adapter tests.

## 3. Contract and verification

- [ ] 3.1 Document the breaking move from `Result.additional_agent_instructions` to response `_meta`, the exact Guide metadata key, FIFO delivery order without priority semantics, and the trial/revert rationale; verify the documentation renders with `mkdocs build --strict`.
- [ ] 3.2 Run focused Result, TaskManager, response-adapter, and public-surface pytest suites in a foreground PTY, then run `ruff check .` and `openspec validate add-response-metadata --strict --no-interactive`; verify all commands pass.
