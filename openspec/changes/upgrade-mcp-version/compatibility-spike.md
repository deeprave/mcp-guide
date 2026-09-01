# FastMCP 4 Compatibility Spike

Date: 2026-08-16

## Selected integration surface

The migration targets the independently maintained **FastMCP 4.0.0b3**, which
builds on the stable MCP Python SDK v2 and protocol revision `2026-07-28`.

The package must be declared and resolved exactly as:

```toml
[project]
dependencies = ["fastmcp==4.0.0b3"]

[tool.uv]
constraint-dependencies = ["fastmcp-slim==4.0.0b3"]
```

The direct `mcp==2.0.0` experiment was rejected. It would repeat the historical
problem of depending on the SDK's server layer instead of FastMCP's separately
maintained public server framework.

The public surface to use is:

- `from fastmcp import Context, FastMCP`
- `FastMCP(name, ...)` and its public tool, prompt, resource, transport, and
  lifecycle APIs
- `from fastmcp.server.sessions import UserSession` only for authenticated
  user-scoped state
- FastMCP's public minted-session API for modern multi-round interactions; Guide
  Session state is in-memory and is not durable across an MCP server restart

## Protocol policy

FastMCP 4 negotiates the best mutually supported protocol per connection. One
Guide server SHALL serve both modern `2026-07-28` and retained handshake-era
clients on stdio and Streamable HTTP. The compatibility suite must therefore
exercise discovery and the public tool, prompt, and resource surfaces in both
eras rather than treat modern requests as rejected.

The wire-level protocol models use SDK v2 snake_case Python fields. FastMCP
provides compatibility bridges for many older camelCase reads, but new Guide
adapters shall use the canonical snake_case fields and public FastMCP APIs.

## State findings

FastMCP 4 makes modern state explicit rather than restoring an invisible
transport session:

- request state carries a multi-round interaction to its next invocation;
- `UserSession` keys server-side state to an authenticated user;
- explicit session identifiers support multiple caller-named buckets; and
- a shared session-state store supports multi-process or durable deployments.

These primitives do not make project roots, client metadata, or an
authenticated user into a valid Guide interaction key. GuideRuntime remains
responsible for resolving and cleaning up Guide Sessions, while each Session
continues to contain its TaskManager. The implementation must select the
appropriate public FastMCP primitive for each cross-request workflow and test
isolation between concurrent agents.

## Implemented modern interaction-state contract

Guide uses FastMCP's public explicit-session API as the sole cross-request
identifier. On a modern `set_project(path)` call, `create_session()` mints the
FastMCP session ID under the current principal and Guide returns that ID in the
standard structured result fixture. The caller supplies the same `session_id`
on each later context-dependent tool or resource request.

Before Guide uses an explicit ID as a `GuideRuntime` owner key, it rejects
empty, overlong, and control-character-bearing values and resolves it with
FastMCP's public `get_session()`. FastMCP rejects unknown IDs and IDs minted
under a different principal; Guide returns a generic invalid-session error and
never creates a replacement Session for either case. Guide does not mint a
second identifier or maintain an ID-to-ID mapping.

`GuideRuntime` owns the in-process lifetime of the resolved Guide Session and
its TaskManager. It evaluates idle expiry at request boundaries (one hour by
default, configurable or disabled by the host), cleans the expired Session and
its owned queues, timers, and cache, and removes its owner entry. FastMCP's
durable session store remains the authoritative validation boundary; a later
valid request may create a fresh, unbound Guide Session after runtime expiry.

Modern requests without an explicit `session_id` remain unbound, except for
the defined `set_project(path)` creation path and the stdio inherited-PWD
bootstrap. They never fall back to client metadata or a connection object.
Retained handshake-era clients are separate: they use the public FastMCP
connection `session_id` compatibility path and are not a modern cross-request
state fallback.

## Compatibility changes requiring migration

- FastMCP 4 removes `ctx.list_roots()` and roots notifications. This is
  intentional: Guide uses explicit `set_project(path)` instead.
- Server-initiated callbacks cannot run within a modern request. Modern follow-up
  requests use the minted FastMCP `session_id` to resolve the live interaction.
- Background tasks are a negotiated extension (`fastmcp-tasks`) and are added
  only when Guide enables task-capable MCP tools.
- Existing code must stop reaching into private FastMCP/MCP session objects.

## Verification pending lockfile update

The dependency declaration now records the FastMCP 4 pin and uv constraint.
The next implementation step is to resolve the lockfile and run isolated
imports and fixture-based modern and legacy clients against the real beta API.
