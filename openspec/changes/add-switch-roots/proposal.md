## Why

An interaction that remains valid while an agent changes repositories must
currently begin a new Guide session, even when it already has the correct
session-owned task and instruction state.  `switch_project` can select another
configuration only within its immutable initial root, which makes ordinary
relative navigation between sibling repositories unavailable.

## What Changes

- Extend `switch_project` with an optional `path` parameter that changes the
  bound client root without changing the Guide session ID.
- Describe `switch_project` as selecting an active configuration project or
  rebinding the project root when `path` is supplied.
- Preserve `name`-only switching as the existing configuration selection within
  the current root.
- Permit a root-switch path to be absolute, current-user anchored (`~`),
  specific-user anchored (`~user`), or relative to the current bound root.
- Select the path basename when `path` is supplied without `name`; allow `name`
  to select a configuration name at the new root when both are supplied.
- Keep `set_project(path)` as the absolute-path-only initial binding operation.
- Ensure a root change refreshes all project-scoped state, including tasks,
  queued instructions, resolved flags, and template context.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guide-project-tools`: `switch_project` accepts an optional root path with
  defined name and path selection semantics.
- `session-management`: a retained Guide Session can atomically replace its
  bound root and active project identity while preserving session ownership.

## Impact

- Affected code: project tool arguments and handlers, Session root and project
  selection, listener notifications, and project-scoped lifecycle tests.
- Affected API: `switch_project` gains optional `path`; existing name-only
  clients remain compatible.
- No dependencies or persisted configuration migration are required.
