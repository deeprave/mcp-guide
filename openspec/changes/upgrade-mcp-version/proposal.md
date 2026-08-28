## Why

`mcp-guide` currently runs on FastMCP 3.4.5 and the Python MCP SDK 1.28.1, with
connection-scoped session state and direct dependence on low-level MCP server
internals. FastMCP 4 is the independently maintained framework built on MCP SDK v2;
it negotiates both protocol eras and supplies supported request/session-state
primitives. A dependency-only upgrade would nevertheless leave Guide's lifecycle,
context, and transport behavior incompatible or fragile.

## What Changes

- Upgrade the current independent FastMCP integration to FastMCP 4, subject to an
  initial compatibility spike that records the exact supported package versions and
  public entry-point calls.
- Redesign server startup and request dispatch around an explicit application runtime,
  public SDK context adapter, and interaction-owned `Session`; remove bootstrap
  `ContextVar`s and patched private MCP server methods.
- Serve both modern `2026-07-28` and retained handshake-era interactions over stdio
  and Streamable HTTP through FastMCP's negotiated dual-protocol support.
- Remove the private roots-notification monkeypatch and all server-pulled roots
  behaviour. Project selection is explicit: when an agent determines its root, it
  invokes Guide's project-selection path with an absolute client filesystem `path`,
  which binds that interaction to the project. The name-only selection argument is
  removed because it cannot identify the agent's project root.
- Update stdio and Streamable HTTP entry points to FastMCP 4 while preserving legacy
  client behavior and adding modern protocol behavior.
- Preserve the public guide tools, prompts, resources, `guide://` scheme, and
  workflow behavior as it exists today across supported clients. The compatibility
  suite will make any protocol-imposed exception explicit; it is not permission to
  silently remove current Guide functionality.
- **BREAKING** Restrict `clone_project` to `clone_project(from_project)` into the
  current active configuration. It shall no longer accept an independently named
  target, which is ambiguous across root-hashed configurations. `from_project` may be
  a unique display name or an exact hash-suffixed configuration key.
- Add protocol-level interoperability and regression coverage for the supported
  transports and context-bearing operations.

## Capabilities

### New Capabilities
- `mcp-v2-request-context`: Defines a framework-neutral context boundary for modern
  request state, legacy connection identity, client metadata, project identity, and
  lifecycle ownership.

### Modified Capabilities
- `mcp-server`: Replace FastMCP 3 initialization assumptions with explicit FastMCP 4
  runtime startup and negotiated protocol dispatch.
- `session-management`: Move Guide session ownership into GuideRuntime while mapping
  both legacy connections and modern supported state to isolated interactions.
- `http-transport`: Use FastMCP 4 Streamable HTTP handling for modern and legacy
  clients.
- `mcp-resources-guide-scheme`: Keep `guide://` resource and command handling
  available through the new resource request context.
- `tool-infrastructure`: Adapt tool invocation and result conversion to public SDK
  response structures and the application context.
- `prompt-infrastructure`: Adapt prompt registration and invocation to the FastMCP 4
  public context.
- `task-manager`: Make queued instructions and project-scoped task lifecycle safe for
  distinct legacy connections without process-global mutable state.

## Impact

- Affected code: `server.py`, `main.py`, `guide.py`, `transports/`, `session.py`,
  `mcp_context.py`, tool/prompt/resource decorators and handlers, result adapters,
  task management, rendering context, and MCP integration tests.
- Dependencies: FastMCP 4 is the direct protocol boundary and brings MCP SDK v2
  transitively. The compatibility spike confirms the exact beta pin and public APIs.
- API and deployment: stdio and HTTP negotiate modern and retained legacy protocol
  revisions. State handling and the beta policy are defined by ADR-011.
- Reference material: the authoritative upstream schema snapshot and a repository
  impact analysis are included with this change.
