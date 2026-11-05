# Proposal

## Why

Guide currently re-probes an enabled project's OpenSpec directory every time a new session starts, despite a current machine-wide OpenSpec state. This creates repeated client busy-work without improving the validity of the configuration gate or the cached CLI version.

## What Changes

- Make a current global `openspec-state` authoritative for an enabled project until its 24-hour expiry: startup and reconnects perform no OpenSpec client request.
- Limit an absent or expired state refresh to `openspec --version`; persist its validation result, parsed version, and fresh timestamp.
- Restrict project initialisation inspection (`openspec/config.yaml`) to an active project flag transition from disabled to enabled, performed through the existing configuration-update queue without gating the version refresh.
- Retire the post-validation project-structure probe and the CLI-location request.
- Preserve on-demand OpenSpec change-list collection for consumers that require it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-manager`: Define quiet startup/reconnect behaviour, daily version refresh, and the configuration-transition verification sequence for OpenSpec.
- `openspec-cli-detection`: Define the version-only refresh request and remove unconditional project-structure detection after validation.

## Impact

- Affected code: `mcp_guide.openspec.task`, its OpenSpec request templates, configuration-update lifecycle, and focused OpenSpec task tests.
- No public tool API, dependency, or project configuration format changes.
