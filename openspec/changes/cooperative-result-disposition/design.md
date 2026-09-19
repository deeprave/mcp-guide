## Context

See proposal.md - Why. Relevant existing mechanics this design builds on:

- `Result` (`src/mcp_guide/core/result.py`) already has `instruction`, `disposition`, and `additional_agent_instructions` fields; `disposition` is set on 5 of 229 construction sites.
- `result_constants.py` defined four disposition constants (`USER_INFO`, `AGENT_INFO`, `AGENT_INSTRUCTION`, `AGENT_REQUIREMENTS`) each mapped to a paired instruction string via `render/frontmatter.py:get_default_instruction_for_type()`. `AGENT_REQUIREMENTS`/`INSTRUCTION_AGENT_REQUIREMENTS` had zero live usages anywhere in the codebase (confirmed by exhaustive grep: no template set `type: agent/requirements`, no code constructed a `Result` with that disposition) — dead plumbing only, never given real meaning at any point. It has since been removed (along with its entries in `frontmatter.py`'s lookup table and `render/cache.py`'s template-context export) rather than defined for the first time; the vocabulary this change works with is three content dispositions (`USER_INFO`, `AGENT_INFO`, `AGENT_INSTRUCTION`), not four.
- `RenderedContent.disposition` (`render/content.py`) already resolves a template's frontmatter `type:` field through `DocumentProperties`, combining parent and partial contributions — the template-to-disposition pipeline exists; most `Result` construction sites simply never wire it through.
- `StartupInstructionListener` (`startup_listener.py`) already renders and queues a `_system/_startup` template exactly once per session, triggered by `on_project_changed`, gated by a `requires-startup-instruction` frontmatter flag. `_system/_onboard_prompt` uses the identical pattern gated by `requires-onboarded: false`. This is a proven, tested, low-risk "teach once per session" mechanism already living in this codebase.
- `combine_instructions` (`content/utils.py`) combines queued instructions by important (`^`-prefixed) vs. regular priority — important instructions replace regular ones entirely (not merged), each list deduplicated by exact string match, then sentence-level deduplication applied to the result. (This corrects an earlier, inexact description of the mechanism as an "override prefix that filters participation" — it is priority-replacement, not selective filtering.)
- This session validated the cooperative-tone pattern (why → what/provenance/scope → action, second person, terse, no third-party "the agent"/"the client" framing) on two real templates: `_system/_filesystem-probe.mustache` and `_system/_project-root.mustache`.

## Goals / Non-Goals

**Goals:**
- Give the agent one place to learn what each disposition means and how to behave, without re-explaining it on every response.
- Make `disposition` alone sufficient for the common case, so most `Result` construction sites can drop their paired prose instruction.
- Prove the pattern on a small, representative pilot before committing to a full 229-site migration.
- Leave `additional_agent_instructions` content untouched in this change; only inventory and flag it.

**Non-Goals:**
- Migrating all `Result` construction sites (tracked as follow-up).
- Rewriting any `additional_agent_instructions` template or string content.
- Changing the transport mechanics of `additional_agent_instructions` (covered by the existing `response-metadata` capability, untouched here).
- Introducing per-disposition "have I explained this yet" state tracking within a session — rejected in favor of a single startup-time teaching document (see Decisions).

## Decisions

### Teaching mechanism: extend the existing startup-template pattern

**Decision:** Add a new `_system/_disposition-guide.mustache` template, rendered and queued once per session by `StartupInstructionListener` alongside the existing `_startup` and `_onboard_prompt` templates, gated by its own `requires-*` flag so it can be independently toggled.

**Why:** `StartupInstructionListener._render_and_queue` already renders exactly this shape of content (a `_system`-category template, queued once at project-bind time) and is tested. Reusing it costs one new template file and one new call in an already-existing loop, rather than new session-state-tracking machinery.

**Alternatives considered:**
- *Per-disposition first-use teaching* (explain `agent/error` the first time it appears in a session, `user/error` the first time that appears, etc.): rejected — needs new per-session state (which dispositions have been explained), more moving parts, and staggers the agent's understanding of the vocabulary across arbitrary points in a session rather than giving it the whole picture up front.
- *On-demand resource* (agent reads a `guide://` URI when it wants the vocabulary): rejected as the sole mechanism — passive, requires the agent to already suspect it needs to look something up; better suited as a secondary reference for re-reading mid-session than as the primary teaching path.
- *Re-stating disposition meaning inline on every response*: this is the status quo's failure mode (redundant prose) and exactly what the proposal is retiring.

### Disposition replaces paired instruction: enforced by rewriting the shared constants, not by new validation

**Decision:** Retire `INSTRUCTION_AGENT_INFORMATION`, `INSTRUCTION_AGENT_INSTRUCTIONS`, and `INSTRUCTION_DISPLAY_ONLY` as paired-with-disposition defaults in `get_default_instruction_for_type()` — return `None` for these three types once the disposition-guide template exists, rather than a bare imperative string. Introduce `INSTRUCTION_AGENT_ERROR` / `INSTRUCTION_USER_ERROR` only if response-specific detail is needed beyond the disposition itself (per the spec's "disposition may stand in place of a prose instruction" requirement); do not give the two error dispositions a generic paired default the way the three content types currently have.

**Why:** The three existing constants exist solely to restate the disposition in prose; once the disposition-guide template teaches that meaning once, the per-response restatement is pure redundancy. The two new error dispositions are different: `agent/error` and `user/error` are structural signals (self-correct vs. stop), but *what specifically* went wrong is response-specific and cannot be a shared constant — that content stays as a per-call `instruction`, now reworded cooperatively per site rather than replaced.

**Alternatives considered:** Keep the three constants but shorten their wording — rejected; per the spec's core principle, the goal is dropping the field, not shrinking it, once the agent already knows the vocabulary.

### Pilot scope: `result_constants.py` helpers plus tool-layer no-project/no-session paths

**Decision:** Migrate `make_no_project_result`, `make_invalid_session_result`, `make_unmintable_session_result` (all in `result_constants.py`, already touched this session for `make_no_project_result`) plus the two or three tool-layer call sites with the highest fan-out (found via the audit task) as the representative pilot.

**Why:** These three helpers are shared across the largest number of call sites (dozens, per this session's earlier grep), so migrating them proves the pattern where it has the most leverage, and `make_no_project_result` already has test coverage this session established (`tests/unit/test_no_project_result.py`) as a template for testing disposition-bearing results.

## Risks / Trade-offs

- **[Risk]** Retiring a shared instruction constant without first confirming every consumer has the disposition-guide content could regress agents that never receive session startup content (e.g., a raw resource/prompt read with no prior tool call in that session). → **Mitigation:** the audit task explicitly checks whether `_check_project_bound`-style early failures can occur before `StartupInstructionListener` has fired for a session, and if so, those specific paths keep a minimal instruction until that ordering is resolved.
- **[Risk]** `combine_instructions`' important/regular replacement semantics mean an important instruction from one queued item silently drops a regular instruction from another; if disposition-only responses stop queuing a regular instruction, an important instruction elsewhere in the same batch is unaffected, but this asymmetry is easy to design around incorrectly. → **Mitigation:** the audit task documents this mechanism precisely (see Context) before any pilot rewiring touches queued-instruction call sites.
- **[Note, not a risk]** `AGENT_REQUIREMENTS`/`agent/requirements` was initially planned as a fourth content disposition with newly-defined semantics (standing/pre-requisite guidance). During this proposal's own audit it was confirmed to have zero live usages anywhere in the codebase, and the decision was reversed: remove the dead constant now rather than retroactively justify keeping it by inventing a use for it. If a genuine need for standing/pre-requisite guidance (distinct from `agent/instruction`'s one-off action) emerges later, it should be proposed fresh, against real call sites, not reintroduced speculatively.

## Open Questions

None — the primary open question from the proposal (how the agent learns the vocabulary) is resolved above (startup-template extension). Migration scope beyond the pilot and `additional_agent_instructions` rewrites are explicitly deferred as follow-up work, not unresolved unknowns within this change.
