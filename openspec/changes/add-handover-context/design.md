# Design

## Context

See proposal.md for motivation and the handoff-context delta specification for
the externally observable contract. Guide already resolves feature flags with
project values taking precedence over global values, renders conditional
template content, and has a project write-policy model. Handoff context is
currently maintained only by convention, including this repository's local
agent instructions.

## Goals / Non-Goals

**Goals:**

- Make proactive handoff prompting an explicit opt-in through one effective
  feature-flag value.
- Resolve one safe target and format description for startup guidance that
  asks agents to maintain the handoff context at milestones.
- Preserve manual user-directed handoff work regardless of flag state.

**Non-Goals:**

- Creating, updating, or monitoring the handoff file server-side.
- Defining the contents or schema of every project's handoff context.
- Changing workflow state, issue tracking, or agent behaviour when the flag is
  absent or false.
- Extending `allowed_write_paths` semantics beyond the existing project policy.

## Decisions

### Resolve a small typed handoff-target value from the effective flag

Interpret false or an absent flag as disabled; interpret true as the document
directory's `context.json`; interpret a string with no directory component as
a document-directory filename; and interpret a relative string with directory
components as a project-relative target. Reject an absolute string. Resolve
this once into a target path, format label, and eligibility state used by the
startup delivery path.

This keeps templates declarative and prevents each delivery point from
reimplementing flag interpretation. Treating strings as arbitrary prose was
rejected because it cannot reliably distinguish a filename from a path.

### Reuse ordinary feature-flag precedence

Use the existing project-then-global resolution rather than adding a dedicated
scope or a second configuration field. This lets a global default serve most
projects while a project can disable it or choose a different target.

Making the setting project-only would prevent the requested global default;
making it global-only would prevent project-specific file conventions.

Register `handoff-context` as a `BOTH`-scope flag beside the existing flag
constants and validators. Its validator accepts absent values for removal,
boolean-like enablement values, or a non-empty target string; its normaliser
uses the existing boolean coercion and preserves a target string for later
path resolution. It rejects an absolute target. Target eligibility remains
project-specific and is therefore validated after ordinary effective-value
resolution, not while a global flag is set.

### Offer explicit project configuration during onboarding

Guided onboarding SHALL offer handoff context as an optional project setting:
disabled (`false`), the default documents-directory target (`true`), or a
valid custom project-relative target. A disabled selection uses an explicit
project `false`, rather than removing the flag, so it overrides an enabled
global default. The onboarding instruction stages the choice for the existing
confirmation step and applies it through the normal project-flag tool. For an
enabled target, onboarding recommends `.gitignore` coverage to avoid routine
handoff updates becoming Git noise, without requiring it because projects may
intentionally share a handoff file.

### Extend StartupTask for queued delivery

Rename `McpUpdateTask` to `StartupTask` and use that existing
TaskManager-owned, one-shot startup task to evaluate both documentation-update
and handoff-context delivery. It SHALL resolve the effective handoff target,
render one dedicated system template, and queue the resulting instruction.

The template has a disabled branch that states no handoff context is set for
the current project. An enabled, eligible branch asks for an updated current
handoff context at the resolved target and in the format implied by its
extension. This keeps delivery copy in templates and avoids hard-coded
instruction strings or a parallel task lifecycle.

### Gate proactive guidance on resolved write eligibility

Resolve the candidate relative target before rendering a startup request, then
use the existing `ReadWriteSecurityPolicy.validate_write_path` check with the
project's `allowed_write_paths`. If it is ineligible, omit the update request
instead of asking an agent to perform a write that policy will reject. This is
a delivery guard, not a new filesystem permission model.

Deferring validation to the agent was rejected because it produces an
actionable-looking request with no authorised destination.

### Derive guidance from the extension without prescribing content

Map common extensions such as `.json`, `.md`, and `.txt` to a format request;
for other extensions, refer to the format implied by the filename. The prompt
asks for an updated, current handoff context but does not impose fields or
prose, preserving project ownership of its contents.

## Risks / Trade-offs

- [A target is absolute or does not pass the project write policy] → omit the
  update request and leave a manual user instruction available.
- [A project expects a richer format than its extension conveys] → the user can
  specify the desired content manually; this feature only supplies format-level
  guidance.
- [Multiple startup delivery paths drift] → use a single resolved target helper and
  one StartupTask rendering path rather than duplicating target interpretation
  or delivery.

## Migration Plan

1. Ship the flag disabled by default, so existing projects receive no new
   startup prompting.
2. Projects that want the current convention can set `handoff-context: true`.
3. Projects needing another location set a filename or safe relative path
   already covered by `allowed_write_paths`.
4. Removing the flag or setting it false immediately restores the default
   no-prompt behaviour; no stored migration is required.
