# ADR-011: FastMCP 4 Protocol Migration

**Status:** Accepted
**Date:** 2026-08-16
**Deciders:** Development Team
**Supersedes:** ADR-002 (MCP Server Framework)
**Related change:** `upgrade-mcp-version`

## Context

`mcp-guide` previously moved from the MCP package's bundled FastMCP to the
separately maintained `fastmcp` package because the bundled implementation had
fallen behind in correctness and capability. That separation remains important.

The modern MCP protocol (`2026-07-28`) removes transport-level sessions, but
Guide must retain application state: the selected project root, a
Session-owned TaskManager, pending instructions, and transient workflow state.
Direct use of the low-level MCP SDK would make Guide responsible for adapting
both protocol eras and for rebuilding stateful application primitives.

FastMCP 4 is independently maintained, builds on MCP SDK v2, and negotiates
the best mutually supported protocol per connection. It supports both modern
sessionless interactions and legacy handshake interactions from one server.
It also supplies the public application primitives needed by this migration:
explicit request state for multi-round interactions, authenticated
`UserSession` state, explicit `SessionId` state where a caller must name a
bucket, durable shared session-state stores, and extension-based background
tasks.

FastMCP 4 is currently beta. Its pre-release dependency must therefore be
pinned exactly, including `fastmcp-slim`, rather than allowing a broad
pre-release resolution.

## Decision

Adopt FastMCP `4.0.0b3` as mcp-guide's protocol integration layer. It SHALL be
the only direct framework dependency at the MCP server boundary; MCP SDK v2 is
transitive through FastMCP.

### Protocol and transport policy

- A single FastMCP server SHALL negotiate and serve both the modern
  `2026-07-28` protocol and retained handshake-era clients on stdio and
  Streamable HTTP.
- Guide SHALL preserve current public tools, prompts, resources, URI handling,
  and response semantics across both negotiated eras unless a documented
  protocol limitation makes a different interaction shape necessary.
- `roots/list` and `roots/list_changed` SHALL not be retained. Project binding
  is explicit through `set_project(path)` for an unbound Guide Session.
- Guide SHALL use FastMCP's supported modern interaction mechanisms instead of
  inventing headers, cookies, or visible context arguments. A modern operation
  requiring a response in a later request uses request state; long-running work
  uses the negotiated tasks extension where applicable.

### Application state

- `GuideRuntime` owns process-shared configuration, docroot, persistent stores,
  and the registry needed to resolve Guide Sessions.
- Each Guide Session owns its TaskManager and all interaction-local state.
- FastMCP `UserSession` is used only where authenticated user state is the
  required scope. It does not replace Guide's separate interaction/session
  boundary for unauthenticated stdio agents or concurrent agents of one user.
- Where the modern protocol needs application state across requests, Guide
  SHALL select a supported explicit FastMCP primitive and record its ownership,
  expiry, and validation rules in the implementation artifacts. It SHALL not
  infer identity from project root, client name/version, or an authenticated
  principal alone.

### Lifecycle and dependency policy

- Server construction and `GuideRuntime` lifecycle SHALL be explicit and
  side-effect-free until startup, using FastMCP's public APIs rather than
  private handlers or monkeypatches.
- The dependency is pinned to `fastmcp==4.0.0b3` and uv constrains
  `fastmcp-slim==4.0.0b3`. Any task-extension dependency is added only when
  Guide enables that extension.
- The migration SHALL test both protocol eras, including state isolation,
  modern request-state continuations, and legacy client compatibility.

## Consequences

### Positive

- Guide keeps the independently maintained framework it adopted to avoid the
  bundled MCP implementation's historical shortfalls.
- Modern MCP v2 capability is available without discarding legacy clients.
- FastMCP owns protocol negotiation and supported state primitives, reducing
  Guide's low-level SDK surface.

### Negative

- FastMCP 4 is beta and requires exact version pinning and an explicit upgrade
  compatibility suite.
- The modern protocol's lack of server callbacks still requires interaction
  redesign for any legacy flow that depends on them; `ctx.list_roots()` is
  removed by FastMCP 4 and is intentionally not replaced.
- Authentication-backed `UserSession` cannot by itself identify unauthenticated
  or concurrent agent interactions, so Guide must retain explicit ownership and
  isolation rules above the framework state store.

## References

- [FastMCP 4 overview](https://gofastmcp.com/getting-started/whats-new)
- [FastMCP 3 to 4 upgrade guide](https://gofastmcp.com/getting-started/upgrading/from-fastmcp-3)
- `openspec/changes/upgrade-mcp-version/compatibility-spike.md`
- ADR-006: Session Management Architecture
