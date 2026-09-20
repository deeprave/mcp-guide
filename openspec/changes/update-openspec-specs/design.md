## Context

See proposal.md - Why. This change audits and corrects `openspec/specs/*/spec.md` files against the current codebase, and splits oversized ones. Relevant facts:

- `openspec validate --specs` and `openspec validate --changes` are separate checks; this change's own deliverable is a clean `--specs` result, distinct from any change's own validation.
- OpenSpec's delta mechanism (`MODIFIED Requirements` with the full original requirement block copied and edited) is the only way to correct a requirement's text without discarding its history at archive time.
- Splitting a spec file changes its file layout, not its normative requirement text. OpenSpec's delta model deltas an existing capability at its existing path; moving requirements between files within a capability, or splitting one capability into several, is a structural operation the standard `MODIFIED`/`ADDED`/`REMOVED` delta vocabulary does not directly describe (those operate on requirement text, not file boundaries).
- Confirmed defect example (see proposal.md and this change's `session-management` delta): specs can describe a design that was never real or has since diverged, undetected because nothing currently checks spec-to-code accuracy automatically.

## Goals / Non-Goals

**Goals:**
- Fix confirmed spec inaccuracies, starting with `session-management`'s no-project-result factory description.
- Establish a repeatable audit method other contributors can apply to the remaining specs this change doesn't finish correcting.
- Split any spec exceeding ~500 lines into smaller files without losing or silently altering requirement content.
- Leave `openspec validate --specs` clean.

**Non-Goals:**
- Auditing every spec to completion in one change — given the number of capabilities (60+) and the acknowledged general staleness, this change prioritizes and phases rather than guarantees full coverage.
- Changing any source code — this change corrects documentation only.
- Resolving the `cooperative-result-disposition` change's ~220-site `Result`/`disposition` migration — that is separate, larger, and gated on that change's own pilot succeeding first.

## Decisions

### Audit priority: subsystems confirmed rewritten first

**Decision:** Audit `session-management`, and any spec describing `GuideRuntime` or `TaskManager` behavior, before working through the rest of the specs tree alphabetically or by size.

**Why:** The user confirmed these three subsystems were completely rewritten — that's the strongest available signal for where specs are most likely stale, stronger than file size or grep hit count alone. Starting here front-loads the highest-value corrections.

**Alternatives considered:** Audit by file size (largest first) — rejected as the primary ordering; size correlates with split-worthiness, not with accuracy risk. Used as a secondary factor once the rewritten-subsystem pass is done.

### Splitting mechanism: reorganize the main spec directly, not through a delta

**Decision:** Spec splitting (moving requirements from one oversized `spec.md` into multiple files, or into a subdirectory under the same capability name) is performed as a direct edit to the files under `openspec/specs/`, not expressed as an `ADDED`/`MODIFIED`/`REMOVED` delta in this change's own `specs/` directory — unless a requirement's text is also being corrected, in which case that correction is a normal delta and the file-location change rides along with it.

**Why:** OpenSpec's delta vocabulary describes requirement-level changes (a requirement was added, its text changed, it was removed, it was renamed) for archival purposes. Pure file reorganization with no requirement-text change has nothing to archive against — there's no "before" requirement text differing from "after." Treating a pure move as a `MODIFIED` delta would force copying unchanged requirement text just to satisfy the delta format, adding noise without adding information. This does mean pure-split-only changes to a spec don't get delta-tracked the way content changes do; that's an accepted limitation of using the delta mechanism for something it wasn't designed to represent.

**Alternatives considered:** Force every split through a `MODIFIED` delta per moved requirement — rejected as needless churn when the requirement text itself isn't changing. Wait for tooling that natively supports move-only deltas — rejected; no such mechanism exists today and waiting blocks the accuracy work this change prioritizes.

### Scope discipline: corrections only where confirmed, not speculative rewrites

**Decision:** Only correct requirement text where the audit finds a specific, demonstrable divergence from the current code (a described function signature that doesn't exist, a described constant that was removed, a described flow that doesn't match the real call chain). Do not rewrite a requirement's wording, restructure its scenarios, or "improve" it stylistically absent a confirmed accuracy defect.

**Why:** This change's purpose is accuracy, not a general spec style pass — conflating the two risks turning a bounded correction effort into an unbounded rewrite of 60+ files, which is explicitly out of scope per the proposal's phased approach.

## Risks / Trade-offs

- **[Risk]** A partial audit (some specs corrected, most not yet touched) could give a false impression that the remaining specs are trustworthy once this change merges. → **Mitigation:** tasks.md's audit output explicitly lists every spec checked and its verdict (accurate / needs correction / not yet audited), so the untouched ones are visibly flagged as unverified rather than silently implied to be fine.
- **[Risk]** Splitting a spec incorrectly (e.g. separating two requirements that depend on shared context) could make the split files individually confusing even though `openspec validate --specs` still passes structurally. → **Mitigation:** keep each split capability's `## Purpose` and any requirement cross-references intact; validate readability, not just validator-passing, by re-reading each split file standalone before considering it done.
- **[Risk]** Fixing `session-management` here creates a second source of truth for that requirement alongside `cooperative-result-disposition`'s own description of the same `make_no_project_result` behavior in its proposal/design, if both changes are open simultaneously. → **Mitigation:** this change's `session-management` delta is the authoritative spec-level correction; `cooperative-result-disposition`'s references to the same behavior are proposal/design narrative, not a competing delta to the same spec file, so there's no merge conflict at the delta level — only a documentation consistency check worth doing once both changes land.

## Migration Plan

No runtime migration — this is a documentation-only change. Sequencing: land this change's `session-management` correction independent of `cooperative-result-disposition`'s implementation progress, since the corrected description matches what's already been implemented and merged into `src/` this session, not something still pending.

## Open Questions

None — audit prioritization, splitting mechanism, and scope discipline are resolved above. The extent of the remaining (non-`session-management`) audit is intentionally left to tasks.md's phased structure rather than fully enumerated here, per the proposal's explicit phased-scope decision.
