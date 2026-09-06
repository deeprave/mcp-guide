## Why

Guide currently uses server-side `LazyPath` expansion for client-supplied project
roots. In a remote or containerised deployment, `~`, `~user`, environment
variables, and filesystem resolution therefore describe the Guide host rather
than the MCP client's filesystem. This can silently bind a different project
than the client intended.

## What Changes

- Add an explicit, process-wide client-filesystem sharing state to `LazyPath`.
  It starts as `None`, which is safely treated as not shared if consulted before
  startup has made its decision; startup explicitly sets it to `True` or
  `False` independently of MCP transport.
- Add `LazyPath.client_resolve()` as the single resolution boundary for
  client-supplied filesystem paths. It may use normal server expansion and
  resolution only when the configured deployment guarantees a shared
  filesystem.
- In non-shared (and not-yet-configured) deployments, reject client-relative
  and user-anchored paths rather than interpreting them on the Guide host. Keep
  client paths lexical: do not expand server environment variables or follow
  server-visible symlinks.
- Route project-root binding, root rebinding, root identity, and the opt-in
  inherited-PWD shortcut through the client-resolution contract. Preserve
  server-owned configuration and docroot resolution through existing
  `LazyPath.resolve()` behaviour.
- Keep local `file://` project URIs percent-decoded before client-path
  validation, without treating URI paths as server filesystem lookups.
- Update user documentation to distinguish client-path resolution from
  server-owned configuration and documentation paths.

## Capabilities

### New Capabilities

- `client-path-resolution`: Process-configured resolution rules for
  client-supplied filesystem identity.

### Modified Capabilities

- `guide-project-tools`: Initial project binding and retained root rebinding
  must honour the client-filesystem sharing contract.
- `mcp-v2-request-context`: The opt-in inherited-PWD bootstrap must only bind a
  root when that path is valid under the configured client-resolution contract.
- `request-context`: Bound root identities must preserve lexical client-path
  semantics without server filesystem expansion or symlink resolution when
  filesystems are not shared.

## Impact

- Affects `LazyPath`, runtime/session startup, project configuration identity,
  and project-selection tools.
- Adds deployment configuration for the filesystem-sharing decision; it must
  not be inferred from stdio, HTTP, or HTTPS transport.
- Changes remote/separate-filesystem behaviour: agents must provide absolute
  client paths rather than `~`, `~user`, or relative paths.
