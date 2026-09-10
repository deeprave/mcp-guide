## Why

Initial stdio project binding currently writes a verification file below the
caller-supplied project root before filesystem sharing has been established.
That write is unnecessary trust in an unverified path, even though the probe
name is random and clean-up is attempted.

## What Changes

- Move the one-shot stdio filesystem-sharing probe from the client-supplied
  project root to an exclusively created server-owned file directly beneath
  the system-wide `/tmp` shareable base.
- Preserve the existing exact-path, secret-content, one-shot response protocol
  and conservative unshared fallback when verification cannot complete.
- Explicitly prohibit probe creation, modification, and clean-up beneath an
  unverified client project root.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `client-path-resolution`: Make initial stdio filesystem-sharing verification
  use only server-owned probe storage rather than the unverified bound root.

## Impact

- Affects `src/mcp_guide/tasks/filesystem_probe.py` and its task-manager tests.
- Initial stdio binding remains lexical and non-failing; the observable probe
  instruction will name a readable server-owned `/tmp` path rather than a path
  in the selected project.
