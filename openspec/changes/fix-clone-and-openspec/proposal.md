## Why

`clone_project` currently copies only categories and collections, so a recovered or
new project loses important project configuration such as feature flags, filesystem
permissions, and exports. OpenSpec CLI metadata is also stored separately for every
project configuration even though the installed CLI is a machine-wide concern.

## What Changes

- Make `clone_project` copy all transferable project configuration, while retaining
  the destination project's identity fields.
- Move OpenSpec validation and version metadata from individual project entries to
  the global structured `openspec-state` feature flag, while retaining the
  per-project `project_flags.openspec` enablement setting.
- Add global `openspec-state.checked`, a decimal UTC Unix timestamp string that
  limits OpenSpec version checks to once every 24 hours.
- Treat `project_flags.openspec` as the exclusive per-project enablement gate;
  when it is enabled and global CLI state is absent, initialise that global state
  by checking availability and version and recording the check timestamp.
- Remove existing per-project OpenSpec metadata without migrating it; an enabled
  project obtains fresh machine-wide CLI state through its normal OpenSpec task.
- **BREAKING**: OpenSpec validation and version fields are no longer stored within
  individual project configuration entries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guide-project-tools`: Clone all transferable project configuration into the
  currently bound destination.
- `config-manager`: Retire legacy per-project OpenSpec metadata without copying
  it; enabled projects initialise global state through their normal checks.
- `feature-flags`: Define the global-only structured OpenSpec state flag and
  project-only OpenSpec enablement flag.
- `models`: Remove per-project OpenSpec metadata.
- `task-manager`: Refresh OpenSpec version information at most once per 24 hours.
- `template-context`: Render OpenSpec state from global configuration rather than
  a project entry.

## Impact

- Affects project cloning, YAML configuration serialisation and migration, OpenSpec
  startup/task behaviour, templates, and their tests.
- Existing project flags and related configuration will be preserved by cloning.
  OpenSpec enablement remains a project-level choice, so globally available CLI
  state does not enable OpenSpec for every project.
