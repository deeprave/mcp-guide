## Context

`LazyPath` currently represents server-owned paths and expands `~`, `~user`, and
environment variables before optional filesystem resolution. Project roots and
request root identity reuse that behaviour even though they originate from an
MCP client and may name a different filesystem. See [proposal.md](proposal.md)
for the motivation and the delta specifications for the behavioural contract.

## Goals / Non-Goals

**Goals:**

- Make filesystem ownership explicit at the path API boundary.
- Configure client/server filesystem sharing once during server startup.
- Retain normal server resolution for configuration, docroot, installation, and
  other server-owned paths.
- Preserve lexical client-root identity when filesystems are separate.

**Non-Goals:**

- Inferring shared filesystems from MCP transport, client metadata, host names,
  or Docker detection.
- Providing client-home lookup or environment expansion for a remote client.
- Supporting a single Guide process that applies different sharing policies to
  different clients.

## Decisions

### Process-wide tri-state policy on LazyPath

`LazyPath` will own a class-level client-filesystem sharing state and a startup
configuration method. The state begins as `None`; `client_resolve()` treats that
as separate for safety. Server startup sets it explicitly to `True` or `False`
from an explicit deployment setting, irrespective of stdio, HTTP, or HTTPS.

This is process-wide because one server deployment has one filesystem contract.
Passing a Boolean at every call site would allow inconsistent policy and obscure
the client/server boundary. A per-transport policy is rejected because either
transport can be local/shared or remote/containerised.

### Separate client resolution from server resolution in the same type

`LazyPath.resolve()` remains the server-path operation: it expands user and
environment values and resolves filesystem links. `LazyPath.client_resolve()`
will be the only operation for client-root identity. In a shared deployment it
delegates to the normal server resolver. In a separate or unconfigured
deployment it rejects user-anchored and relative inputs, does not expand
environment variables, and lexically normalises an absolute path without
filesystem access.

Keeping both methods on `LazyPath` makes the caller's filesystem authority
visible while preserving existing server-path behaviour. A separate client-path
class or helper is rejected because it permits the old ambiguous path API to
remain in use at client boundaries.

### Preserve retained root-relative switching only for shared filesystems

`switch_project(path=...)` will first identify a relative input. It rejects that
input for separate or unconfigured filesystems. For shared filesystems it joins
the path to the current bound root before invoking `client_resolve()`, retaining
the existing root-relative switch contract rather than resolving against an
unrelated process working directory.

### Keep URI decoding at the project-input boundary

Project-tool input parsing will decode a local `file://` URI before creating a
`LazyPath`. URI syntax is not a generic filesystem path concern. The decoded
path then follows `client_resolve()` like every other client root.

### Startup configuration surface

The server CLI configuration will expose an explicit global client-filesystem
sharing option (with an environment-variable equivalent). Its default value is
separate. The `LazyPath` class still begins as `None` until startup consumes this
configuration, allowing early use to fail closed and tests to assert lifecycle
initialisation.

## Risks / Trade-offs

- [A shared deployment is misconfigured as separate] → Agents must send
  absolute roots; no incorrect host path is selected.
- [A separate deployment is misconfigured as shared] → Host expansion could be
  used incorrectly; documentation and an explicit opt-in option make this a
  deployment operator responsibility.
- [Existing clients send `~` or relative roots remotely] → Return a precise
  invalid-path response directing them to resolve and send an absolute client
  path.
- [Tests leak global policy between cases] → Reset the tri-state configuration
  in test fixtures and cover all three state values.

## Migration Plan

1. Introduce the startup setting and initialise the global state at server
   startup.
2. Route client project-root paths through `client_resolve()` and update the
   PWD bootstrap condition.
3. Update agent-facing documentation and regression coverage.
4. Roll back by configuring a known shared deployment as shared; no persisted
   project configuration schema changes are required.
