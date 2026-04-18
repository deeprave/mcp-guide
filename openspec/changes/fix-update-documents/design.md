## Context

The startup reminder path for documentation updates currently decides whether to
queue an acknowledged `update_documents` instruction without applying the same
gating rules enforced by the actual installer/update path.

This creates a mismatch between:

- `McpUpdateTask`, which can currently prompt for an update based only on
  version-comparison flow
- installer safety validation, which already rejects unsafe update targets such
  as a `docroot` equal to the template source directory

The bug is triggered when the project has a configured documentation root that
exists, but is not a valid installed-docs target. In particular, startup
prompting should not occur when the installed docs version marker is missing or
when the resolved docroot is the template source directory.

This change touches cross-module behavior because prompt queuing lives in the
task layer while docroot safety knowledge already exists in the installer
module.

## Goals / Non-Goals

**Goals:**
- Ensure startup update prompting uses the same effective validity checks as the
  actual update path
- Prevent acknowledged update reminders from being queued for non-updatable
  docroot configurations
- Reuse existing installer-side docroot validation instead of introducing a
  second independent safety rule
- Treat a missing `{docroot}/.version` file as “not installed / not updatable”
  for startup prompting purposes

**Non-Goals:**
- Changing the installer’s existing safety behavior
- Redesigning the update reminder workflow or acknowledgement model
- Adding new user-facing configuration for documentation updates
- Inferring or reconstructing installed version state when `.version` is absent

## Decisions

- Reuse installer-side docroot validation before startup prompt queuing.
  - Rationale: the updater already has the authoritative safety rule for
    whether a docroot is updatable. Reusing that logic avoids drift between
    prompt-time and execution-time behavior.
  - Alternative considered: duplicate the `docroot != template source` check in
    `McpUpdateTask`. Rejected because it creates two rules that can diverge.

- Gate prompting on the presence of `{docroot}/.version`.
  - Rationale: startup prompting is meaningful only when there is an existing
    installed-docs state to compare against the package version. If the version
    file is absent, prompting should be skipped rather than treated as an
    actionable update.
  - Alternative considered: treat a missing version file as “outdated” and
    prompt anyway. Rejected because this is the exact false-positive path that
    currently produces guaranteed failure.

- Evaluate updateability before version comparison.
  - Rationale: invalid docroot states should short-circuit early and avoid
    unnecessary file reads or version logic.
  - Alternative considered: keep current ordering and suppress only after a
    failed comparison or missing file read. Rejected because it keeps more of
    the invalid path alive than needed.

- Treat invalid docroot states as silent no-prompt outcomes.
  - Rationale: the startup reminder mechanism should surface only actionable
    work. Unsafe or incomplete installation state is not actionable via
    `update_documents`.
  - Alternative considered: queue a different warning-style reminder. Rejected
    as out of scope for this bug fix.

## Risks / Trade-offs

- [Cross-module coupling] `McpUpdateTask` will depend more directly on
  installer validation behavior → Mitigation: reuse a narrow helper with stable
  semantics instead of reaching into broader installer internals.
- [Behavior tightening] Some environments that previously prompted will now do
  nothing → Mitigation: this is the intended correction because those prompts
  were false positives.
- [Missing-file ambiguity] A missing `.version` could reflect a broken
  installation rather than “never installed” → Mitigation: still treat it as
  non-updatable for prompting, leaving installer/update operations to remain
  the enforcement point when explicitly invoked.
- [Regression risk] Prompt gating and installer safety could still drift later
  if validation logic is copied elsewhere → Mitigation: add regression tests at
  the task/prompt layer for boolean prompt/no-prompt outcomes.

## Migration Plan

- No migration or rollout steps are required.
- Implement the gating change in `McpUpdateTask`.
- Reuse the installer-side docroot validation helper or extract a shared helper
  if needed without changing existing installer semantics.
- Add tests for:
  - unsafe docroot equal to template source
  - missing `{docroot}/.version`
  - valid installed docs with differing version still prompting
- Rollback, if required, is a simple reversion of the task-layer gating change.

## Open Questions

- Does the existing installer validation helper already have the right shape for
  direct reuse by `McpUpdateTask`, or should a smaller shared helper be
  extracted first?
- Are there any other “non-updatable but existing” docroot states that should
  also be treated as no-prompt conditions beyond template-source equivalence and
  missing `.version`?
