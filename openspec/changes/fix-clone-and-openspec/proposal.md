## Why

`clone_project` currently copies only categories and collections, so a recovered or
new project loses important project configuration such as feature flags, filesystem
permissions, and exports. OpenSpec CLI metadata is also stored separately for every
project configuration even though the installed CLI is a machine-wide concern.

## What Changes

- Make `clone_project` copy all transferable project configuration, while retaining
  the destination project's identity fields.
- Move OpenSpec validation and version metadata from individual project entries to a
  global `openspec` configuration block.
- Add global `openspec.checked`, a UTC Unix timestamp float that limits OpenSpec
  version checks to once every 24 hours.
- Migrate existing per-project OpenSpec metadata safely, without treating a
  conflicting legacy value as authoritative.
- **BREAKING**: OpenSpec validation and version fields are no longer stored within
  individual project configuration entries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guide-project-tools`: Clone all transferable project configuration into the
  currently bound destination.
- `config-manager`: Persist and migrate machine-wide OpenSpec state alongside
  global feature flags.
- `models`: Remove per-project OpenSpec metadata and model the global OpenSpec
  state.
- `task-manager`: Refresh OpenSpec version information at most once per 24 hours.
- `template-context`: Render OpenSpec state from global configuration rather than
  a project entry.

## Impact

- Affects project cloning, YAML configuration serialisation and migration, OpenSpec
  startup/task behaviour, templates, and their tests.
- Existing project flags and related configuration will be preserved by cloning.
