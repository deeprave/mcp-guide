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

### Teaching mechanism: deliver guidance with startup

**Decision:** Deliver the disposition guide as part of startup guidance, once per bound session.

**Why:** Startup already provides the tested, low-risk point at which to teach important Guide behaviour once per bound session, avoiding new session-state tracking.

**Alternatives considered:**
- *Per-disposition first-use teaching* (explain `agent/error` the first time it appears in a session, `user/error` the first time that appears, etc.): rejected — needs new per-session state (which dispositions have been explained), more moving parts, and staggers the agent's understanding of the vocabulary across arbitrary points in a session rather than giving it the whole picture up front.
- *On-demand resource* (agent reads a `guide://` URI when it wants the vocabulary): rejected as the sole mechanism — passive, requires the agent to already suspect it needs to look something up; better suited as a secondary reference for re-reading mid-session than as the primary teaching path.
- *Re-stating disposition meaning inline on every response*: this is the status quo's failure mode (redundant prose) and exactly what the proposal is retiring.

### Disposition replaces paired instruction: remove the default mechanism entirely, don't just neuter it

**Decision (as shipped, revised twice during implementation):** `get_default_instruction_for_type()` now always returns `None` — its per-type lookup table is gone, not just emptied. More significantly, the application-level blanket default mechanism it fed into is removed entirely: `Result.default_success_instruction`/`default_failure_instruction` class vars, their classmethods, and `mcp_guide/result.py`'s import-time assignment of `INSTRUCTION_DISPLAY_ONLY`/`INSTRUCTION_ERROR_MESSAGE` as universal defaults are all deleted. A `Result` with no explicit `instruction=` now has none at all — correctly omitted from `to_json()` — rather than acquiring a generic one regardless of what it actually contains.

**A parallel mechanism was tried and reverted:** mid-implementation, `default_success_disposition`/`default_failure_disposition` class vars were added to give `disposition` the same blanket-default treatment the instruction fields used to have (`agent/information` for success, a new `unknown/error` for failure). This was corrected: disposition must stay *situational* — set only where content genuinely has a knowable one (a rendered document, skill, or command) — never blanket-applied regardless of content, which would fabricate meaning `Result.ok()`/`.failure()` has no basis for. `disposition=None` is a valid, meaningful `Result` state, not a gap to paper over. `UNKNOWN_ERROR = "unknown/error"` remains defined as available vocabulary for call sites that want to say "this failed, audience not yet classified," but nothing applies it automatically.

**Per-category defaults, verified rather than built:** the concern that removing defaults would leave skills/commands/documents without sensible per-category dispositions turned out to already be handled by existing code, unrelated to the (reverted) `Result`-level mechanism: `RenderedContent.__post_init__` still hardcodes `disposition_default=AGENT_INSTRUCTION` at construction time (unchanged, correct for skills and commands, confirmed live against this session's own `guide://$workflow-implement` call); `resolve_content_properties()` in `content/utils.py` already calls `.with_disposition_default(USER_INFO)` when combining files for document delivery (used by both `tool_content.py` and `tool_category.py`). No new plumbing was needed for this.

Introduce `INSTRUCTION_AGENT_ERROR` / `INSTRUCTION_USER_ERROR` only if response-specific detail is needed beyond the disposition itself (per the spec's "disposition may stand in place of a prose instruction" requirement); do not give the two error dispositions a generic paired default the way the three content types used to have.

**Why:** The three retired constants existed solely to restate the disposition in prose; once the disposition-guide template teaches that meaning once, the per-response restatement is pure redundancy — removing the mechanism outright, rather than leaving a `None`-returning stub, avoids leaving dead indirection in the codebase (`get_type_based_default_instruction`'s wrapper chain would otherwise have become a pure pass-through with no logic left in it). Keeping disposition situational (not blanket-defaulted) preserves the same principle that made removing the instruction defaults worthwhile in the first place: a field should reflect what's actually known about the content, not a guess applied indiscriminately.

**Alternatives considered:** Keep the three constants but shorten their wording — rejected; the goal is dropping the field, not shrinking it. Give `Result` a blanket disposition default mirroring the removed instruction defaults — tried, reverted; disposition needs to stay `None` when genuinely unknown, exactly the property the old instruction-default mechanism lacked and that motivated retiring it.

### Pilot scope: `result_constants.py` helpers plus tool-layer no-project/no-session paths

**Decision:** Migrate `make_no_project_result`, `make_invalid_session_result`, `make_unmintable_session_result` (all in `result_constants.py`, already touched this session for `make_no_project_result`) plus the two or three tool-layer call sites with the highest fan-out (found via the audit task) as the representative pilot.

**Why:** These three helpers are shared across the largest number of call sites (dozens, per this session's earlier grep), so migrating them proves the pattern where it has the most leverage, and `make_no_project_result` already has test coverage this session established (`tests/unit/test_no_project_result.py`) as a template for testing disposition-bearing results.

## Risks / Trade-offs

- **[Risk]** Retiring a shared instruction constant without first confirming every consumer has the disposition-guide content could regress agents that never receive session startup content (e.g., a raw resource/prompt read with no prior tool call in that session). → **Mitigation:** the audit task explicitly checks whether `_check_project_bound`-style early failures can occur before `StartupInstructionListener` has fired for a session, and if so, those specific paths keep a minimal instruction until that ordering is resolved.
- **[Risk]** `combine_instructions`' important/regular replacement semantics mean an important instruction from one queued item silently drops a regular instruction from another; if disposition-only responses stop queuing a regular instruction, an important instruction elsewhere in the same batch is unaffected, but this asymmetry is easy to design around incorrectly. → **Mitigation:** the audit task documents this mechanism precisely (see Context) before any pilot rewiring touches queued-instruction call sites.
- **[Note, not a risk]** `AGENT_REQUIREMENTS`/`agent/requirements` was initially planned as a fourth content disposition with newly-defined semantics (standing/pre-requisite guidance). During this proposal's own audit it was confirmed to have zero live usages anywhere in the codebase, and the decision was reversed: remove the dead constant now rather than retroactively justify keeping it by inventing a use for it. If a genuine need for standing/pre-requisite guidance (distinct from `agent/instruction`'s one-off action) emerges later, it should be proposed fresh, against real call sites, not reintroduced speculatively.

## Open Questions

None — the primary open question from the proposal (how the agent learns the vocabulary) is resolved above (startup-template extension). Migration scope beyond the pilot and `additional_agent_instructions` rewrites are explicitly deferred as follow-up work, not unresolved unknowns within this change.
