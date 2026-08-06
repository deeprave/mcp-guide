## Why

`mcp-guide` currently runs on FastMCP 3.4.5 and the Python MCP SDK 1.28.1, with
connection-scoped session state and direct dependence on FastMCP and low-level MCP
server internals. The MCP SDK v2.0.0 / protocol revision 2026-07-28 replaces the
legacy initialization and connection model with negotiated, request-scoped protocol
handling, so a dependency-only upgrade would leave core lifecycle, context, and
transport behavior incompatible or fragile.

## What Changes

- Upgrade the MCP and FastMCP integration to versions that support MCP protocol
  revision 2026-07-28, with an explicit supported-version policy.
- **BREAKING** Redesign server startup and request dispatch around a request-scoped
  application context instead of a mutable connection-bound `Session`, bootstrap
  `ContextVar`s, and patched private MCP server methods.
- **BREAKING** Redesign project, client, roots, and agent context resolution so it
  works for stateless and multi-round-trip requests without relying on a client
  connection object.
- Replace direct use of legacy roots notifications and server-initiated requests
  with the standard v2-compatible mechanism selected during design, while preserving
  project re-binding behavior where the client provides equivalent information.
- Update stdio and Streamable HTTP entry points, request validation, response
  metadata, and caching behavior to the new protocol requirements.
- Preserve the public guide tools, prompts, resources, `guide://` scheme, and
  workflow behavior where the selected protocol capability permits it; document any
  intentionally removed legacy behavior and migration path for clients.
- Add protocol-level interoperability and regression coverage for the supported
  transports and context-bearing operations.

## Capabilities

### New Capabilities
- `mcp-v2-request-context`: Defines a protocol-version-aware, request-scoped context
  boundary for client metadata, project identity, request state, and lifecycle
  ownership.

### Modified Capabilities
- `mcp-server`: Replace legacy connection initialization assumptions with negotiated
  protocol startup and request dispatch.
- `session-management`: Replace connection-lifetime session ownership with an
  explicit context/state model compatible with stateless requests.
- `http-transport`: Meet modern Streamable HTTP headers, version negotiation, and
  response semantics.
- `mcp-resources-guide-scheme`: Keep `guide://` resource and command handling
  available through the new resource request context.
- `tool-infrastructure`: Adapt tool invocation and result conversion to modern MCP
  response structures and per-request context.
- `prompt-infrastructure`: Adapt prompt registration and invocation to the new
  request context and remove dependence on legacy initialization data.
- `task-manager`: Make queued instructions and project-scoped task lifecycle safe
  when requests are stateless and no server connection object is available.

## Impact

- Affected code: `server.py`, `main.py`, `guide.py`, `transports/`, `session.py`,
  `mcp_context.py`, tool/prompt/resource decorators and handlers, result adapters,
  task management, rendering context, and MCP integration tests.
- Dependencies: FastMCP and the Python MCP SDK will require coordinated upgrades;
  their exact compatible versions and migration APIs will be confirmed during
  implementation.
- API and deployment: stdio and HTTP clients may need a supported protocol revision
  and updated transport headers. Any retained legacy compatibility will be explicit
  and tested rather than an accidental side effect.
- Reference material: the authoritative upstream schema snapshot and a repository
  impact analysis are included with this change.
