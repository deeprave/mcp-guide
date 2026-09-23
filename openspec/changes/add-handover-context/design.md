# Design

## Context

See proposal.md for motivation and the handover-context delta specification for
the externally observable contract. Guide already resolves feature flags with
project values taking precedence over global values, renders conditional
template content, and has a project write-policy model. Handover context is
currently maintained only by convention, including this repository's local
agent instructions.

## Goals / Non-Goals

**Goals:**

- Make proactive handover prompting an explicit opt-in through one effective
  feature-flag value.
- Resolve one safe target and format description that milestone guidance can
  reuse.
- Preserve manual user-directed handover work regardless of flag state.

**Non-Goals:**

- Creating, updating, or monitoring the handover file server-side.
- Defining the contents or schema of every project's handover context.
- Changing workflow state, issue tracking, or agent behaviour when the flag is
  absent or false.
- Extending `allowed_write_paths` semantics beyond the existing project policy.

## Decisions

### Resolve a small typed handover-target value from the effective flag

Interpret false or an absent flag as disabled; interpret true as the document
directory's `context.json`; interpret a string with no directory component as
a document-directory filename; and interpret a relative string with directory
components as a project-relative target. Resolve this once into a target path,
format label, and eligibility state used by all milestone delivery paths.

This keeps templates declarative and prevents each delivery point from
reimplementing flag interpretation. Treating strings as arbitrary prose was
rejected because it cannot reliably distinguish a filename from a path.

### Reuse ordinary feature-flag precedence

Use the existing project-then-global resolution rather than adding a dedicated
scope or a second configuration field. This lets a global default serve most
projects while a project can disable it or choose a different target.

Making the setting project-only would prevent the requested global default;
making it global-only would prevent project-specific file conventions.

### Gate proactive guidance on resolved write eligibility

Resolve the candidate target before rendering a milestone request, then use
the existing project-root and allowed-write-path checks. If it is ineligible,
omit the guidance instead of asking an agent to perform a write that policy
will reject. This is a delivery guard, not a new filesystem permission model.

Deferring validation to the agent was rejected because it produces an
actionable-looking request with no authorised destination.

### Derive guidance from the extension without prescribing content

Map common extensions such as `.json`, `.md`, and `.txt` to a format request;
for other extensions, refer to the format implied by the filename. The prompt
asks for an updated, current handover context but does not impose fields or
prose, preserving project ownership of its contents.

## Risks / Trade-offs

- [A target is configured outside the project without write permission] → omit
  proactive guidance and leave a manual user instruction available.
- [A project expects a richer format than its extension conveys] → the user can
  specify the desired content manually; this feature only supplies format-level
  guidance.
- [Multiple milestone paths drift] → use a single resolved target helper and
  shared conditional partial rather than duplicating target interpretation.

## Migration Plan

1. Ship the flag disabled by default, so existing projects receive no new
   milestone prompting.
2. Projects that want the current convention can set `handoff-context: true`.
3. Projects needing another location set a filename or safe relative path.
4. Removing the flag or setting it false immediately restores the default
   no-prompt behaviour; no stored migration is required.
