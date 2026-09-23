# Proposal

## Why

Agents currently maintain handoff context by project convention, which makes
the behaviour implicit and can produce prompting even when a project does not
want it. Projects need an explicit, scoped opt-in that tells agents where to
keep concise current handoff state, while leaving manual user-directed
handoff unchanged.

## What Changes

- Add a `handoff-context` feature flag that can be set globally or per project.
- Validate and normalise the flag through the established feature-flag
  registration path; project values override global values.
- Make the default false: Guide queues a rendered informational message that no
  handoff context is configured, rather than requesting an update.
- Support `true` as the default `context.json` target under
  `{{paths.documents}}`, a filename as a document-directory target, and a
  project-relative path as an explicit target; reject absolute paths.
- Derive the requested handoff format from the target extension, including
  JSON, Markdown, and plain text.
- Require the resolved target to pass the project's existing
  `allowed_write_paths` policy before Guide asks an agent to update it.

## Capabilities

### New Capabilities
- `handoff-context`: Configure and deliver opt-in, safe agent guidance for
  delivering one startup instruction that asks agents to maintain current
  handoff context at milestones.

### Modified Capabilities
- None.

## Impact

- Feature-flag resolution and project configuration.
- Startup guidance and rendered agent instructions.
- The existing TaskManager-owned startup task, renamed `StartupTask` from
  `McpUpdateTask`, rather than a new task.
- Path resolution and write-permission checks for the selected context target.
- Tests for disabled defaults, scope resolution, target selection, format
  guidance, and disallowed locations.
