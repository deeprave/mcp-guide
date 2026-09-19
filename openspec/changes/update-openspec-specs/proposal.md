## Why

Guide has moved substantially past its original v1 implementation — it now targets MCP protocol `2026-07-28` (with legacy-protocol considerations retained), and Session management, `GuideRuntime`, and `TaskManager` were completely rewritten. Many OpenSpec capability specs under `openspec/specs/` no longer accurately describe the current implementation. At least one confirmed defect exists: `session-management`'s "Async factory for no-project result" requirement describes a `make_no_project_result(ctx)` signature that calls `get_session(ctx)` internally and mandates that `RESULT_NO_PROJECT` never be removed — none of which matches the real, current, zero-argument, session-less design (confirmed and partly superseded during the `cooperative-result-disposition` change, which removed `RESULT_NO_PROJECT` after confirming it had zero remaining callers). Several other specs (e.g. `template-rendering`, `category-tools`) have also grown past a size that's comfortable to review or keep accurate, mixing many loosely related requirements in one file.

## What Changes

- Audit every spec under `openspec/specs/` for accuracy against the current codebase, prioritized by known risk: session/runtime/task-manager-related capabilities first (since those subsystems were confirmed completely rewritten), then the rest.
- Correct `session-management`'s "Async factory for no-project result" requirement to describe the real design: `make_no_project_result()` takes no arguments, renders `_system/_project-root` with `session=None` (no session lookup, no `ctx`), caches the render once per process on `GuideRuntime`, and falls back to the static `INSTRUCTION_NO_PROJECT` string (not a `RESULT_NO_PROJECT` object, which no longer exists) when rendering is unavailable.
- Split specs that exceed a practical size (target: under ~500 lines) along natural requirement/capability boundaries, preserving every existing requirement's content — this is reorganization, not requirement removal, unless a requirement is found to be genuinely obsolete during the audit (tracked separately as a REMOVED delta with justification, not silently dropped).
- Achieve a clean `openspec validate --specs` result across the whole specs tree.
- Reconcile, where the audit finds it practical, spec descriptions of `Result`-returning behavior against the `disposition` field introduced by `cooperative-result-disposition` — but do not block this change on that migration completing; the ~220 non-pilot `Result` construction sites are separate, larger follow-up work this change may note but does not need to resolve.

This is deliberately scoped as a first, prioritized pass rather than an exhaustive one-shot fix of every spec in the tree — the audit may surface more inaccuracies than can be corrected in a single change; those get recorded as explicit follow-up rather than silently left for someone to rediscover.

## Capabilities

### New Capabilities
(none — this change corrects and reorganizes existing capability specs; it does not introduce new system behavior)

### Modified Capabilities
- `session-management`: "Async factory for no-project result" requirement corrected to match the actual `make_no_project_result()` signature and behavior (see What Changes).
- Additional capabilities identified during the audit as materially inaccurate will be added here as the audit proceeds, each with its own delta describing the corrected requirement. (Capabilities requiring only splitting, with no accuracy correction, do not need a delta here — reorganizing a spec's file layout without changing its normative content is not a requirements change; see design.md for how splitting without a corresponding delta is handled.)

## Impact

- `openspec/specs/session-management/spec.md` — corrected requirement text for the no-project-result factory.
- Additional `openspec/specs/*/spec.md` files — corrected and/or split, scope determined by the audit (task 1 in tasks.md).
- No source code changes — this change corrects documentation of existing behavior; it does not alter `src/mcp_guide/*`.
