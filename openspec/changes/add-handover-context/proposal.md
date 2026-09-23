# Proposal

## Why

Agents currently maintain handover context by project convention, which makes
the behaviour implicit and can produce prompting even when a project does not
want it. Projects need an explicit, scoped opt-in that tells agents where to
keep concise current handover state, while leaving manual user-directed
handover unchanged.

## What Changes

- Add a `handoff-context` feature flag that can be set globally or per project.
- Make the default false: Guide does not proactively request handover-context
  updates unless the effective flag enables them.
- Support `true` as the default `context.json` target under
  `{{paths.documents}}`, a filename as a document-directory target, and a
  project-relative path as an explicit target.
- Derive the requested handover format from the target extension, including
  JSON, Markdown, and plain text.
- Require the resolved target to remain within the project or to be covered by
  the project's `allowed_write_paths` before Guide asks an agent to update it.

## Capabilities

### New Capabilities
- `handover-context`: Configure and deliver opt-in, safe agent guidance for
  maintaining current handover context at workflow milestones.

### Modified Capabilities
- None.

## Impact

- Feature-flag resolution and project configuration.
- Workflow milestone guidance and rendered agent instructions.
- Path resolution and write-permission checks for the selected context target.
- Tests for disabled defaults, scope resolution, target selection, format
  guidance, and disallowed locations.
