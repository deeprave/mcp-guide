## Why

Client project paths may belong to a different filesystem from the Guide server.
Server-side expansion can silently interpret user anchors and environment
variables against the wrong host. Verified local stdio operation is a supported
special case, not the default.

## What Changes

- Add process-wide tri-state sharing state to LazyPath and keep client resolution
  on LazyPath.client_resolve(). None and False disable client shorthand.
- Disable sharing for HTTP/HTTPS and never send a probe on those transports.
- For stdio, verify shared access shortly after the first absolute-root binding
  using a one-shot task and a uniquely named file with unpredictable contents.
- Queue an instruction asking the agent to read that exact file and return it
  through send_file_content. Start the approximately 60-second response timeout
  only when the queued instruction is attached to an outgoing response.
- Intercept the exact pending probe path before ordinary content handling, compare
  the returned contents, record the global result, remove the file and unsubscribe.
- Treat successful shared-file verification as sufficient to permit relative
  switching, ~, ~user and $VAR expansion using server semantics. Client information
  may corroborate this; otherwise assume the same user. Do not require separate
  user/environment equivalence verification.
- Reject relative, user-anchored and variable-bearing client paths until verified
  and on HTTP/HTTPS. Accept absolute client paths lexically without server lookups.
- Preserve server-owned configuration/docroot path behaviour and update all
  associated user and agent documentation.

## Capabilities

### New Capabilities

- client-path-resolution: verified stdio sharing and client-aware path resolution.

### Modified Capabilities

- guide-project-tools: binding and switching honour client-path policy.
- mcp-v2-request-context: inherited-PWD bootstrap honours verification state.
- request-context: client root identity follows the selected resolution policy.

## Impact

Affects LazyPath, initial binding, project switching, task registration and
instruction acknowledgement, file-response interception, and path documentation.
No new runtime dependency or explicit sharing CLI override is required.
Docker stdio is not assumed local; remote/containerised HTTP never probes.
No persisted sharing result: each server process starts unverified.
