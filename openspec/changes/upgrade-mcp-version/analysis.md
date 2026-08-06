# MCP v2 Upgrade Analysis

## Target and Evidence

The target is MCP protocol revision `2026-07-28`. The local authoritative schema
snapshot is [`../../std/mcp-schema-2026-07-28.ts`](../../std/mcp-schema-2026-07-28.ts);
SDK "v2.0.0" is the associated major migration line, not the protocol version that
clients negotiate.

The analysis also uses the upstream SDK migration guidance. Exact FastMCP and Python
MCP package versions must be confirmed during the first implementation spike, since
the repository currently resolves FastMCP 3.4.5 and MCP 1.28.1.

## Current Architecture Inventory

| Area | Current implementation | Upgrade implication |
| --- | --- | --- |
| Server entry point | `main.py` creates one `GuideMCP`; transports call `run_stdio_async()` or `streamable_http_app()`. | Replace with the v2-supported server/app factory and retain the CLI transport contract where feasible. |
| Connection lifecycle | `server.py` patches private `_mcp_server._handle_message` and registers a low-level `RootsListChangedNotification` handler. | Remove private monkeypatching and connection-object ownership; modern protocol does not provide the same server-initiated notification/request path. |
| Session ownership | `session.py` combines a task-local `ContextVar` with a `WeakKeyDictionary` keyed by FastMCP `MiddlewareServerSession`. | Separate durable project configuration from explicit, authenticated request/interaction state. No correctness path may require a live SDK session object. |
| Client context | `mcp_context.py` reads `ctx.session.client_params`, calls `ctx.session.list_roots()`, and uses bootstrap `ContextVar`s. | Build an adapter that extracts client metadata, roots, and request state from the v2 request envelope; missing context must be represented explicitly. |
| Project selection | First root and, as a fallback, server `PWD` determine the project. | Bind project identity to the request context or an explicit `set_project` interaction; do not infer a remote client's project from server process state. |
| Resources | `resources.py` reads `ctx.request_context.request.params.uri`. | Keep URI access behind the new request-context adapter so guide resources are independent of a FastMCP private object shape. |
| Results | Tool and prompt wrappers serialize internal `Result` values to JSON strings before FastMCP emits them. | Rework the boundary to produce v2 SDK result/content structures, including protocol metadata and cache directives where applicable. |
| Task manager | A process-local `TaskManager` owns timers, queued instructions, cache, and project-scoped task instances. | Scope queued delivery and project task state to an explicit interaction/project identity; background work must not depend on a connection-local context variable. |

## Protocol Capability Changes and Required Work

### 1. Discovery, negotiation, and stateless execution

The modern protocol uses `server/discover` and version negotiation rather than
assuming a persistent legacy initialization handshake. Requests are self-contained;
the server must declare and enforce a supported protocol-revision policy.

Required work:

- Add a protocol adapter that accepts the modern request envelope and exposes only
  stable application-facing context.
- Rebuild the server entry point around the supported v2 server factory/handler API.
- Remove use of private FastMCP/MCP server attributes and behavior coupled to
  `MiddlewareServerSession`.
- Decide and document whether legacy protocol clients are supported during a
  transition. The default target is modern protocol support; compatibility must be
  explicit, bounded, and tested if retained.

### 2. Request context and state

The legacy design assumes that a client connection carries roots, client parameters,
and mutable `Session` state. Modern requests instead carry context independently and
use request state for multi-round-trip interactions.

Required work:

- Introduce a framework-neutral `RequestContext` carrying protocol revision,
  authenticated client identity (when provided), roots, agent/client metadata,
  selected project, and request method/parameters.
- Replace bootstrap and active-session `ContextVar` state with explicit arguments at
  application boundaries. Context variables may remain as tightly scoped convenience
  bindings, but not as the source of cross-request identity or correctness.
- Represent `set_project` and other stateful interactions with integrity-protected,
  expiry-bound request state where the protocol requires state to round-trip.
- Bind any serialized state to the relevant client/principal, request method and
  parameters (or a documented equivalent) to prevent replay or context substitution.
- Define a predictable no-project result when roots and prior selected state are
  unavailable; never fall back to server `PWD` for a remote client.

### 3. Roots and client-originated changes

The existing roots-change path depends on a server-initiated `list_roots()` request
after a `roots/list_changed` notification. Modern v2 removes the comparable
server-to-client JSON-RPC request channel.

Required work:

- Remove the patched roots-notification handler.
- Refresh project context only when a request supplies roots or valid request state;
  an absent roots update leaves the current interaction state unchanged.
- Replace any needed client input flow with v2 multi-round-trip `inputRequired`
  behavior rather than server-originated JSON-RPC requests.
- Audit sampling, elicitation, roots, and resource subscription use before coding;
  any currently unsupported server-to-client behavior must be either redesigned or
  explicitly retired with migration guidance.

### 4. Transport and HTTP semantics

The existing HTTP wrapper delegates to FastMCP's Streamable HTTP application but has
no application-level policy for modern protocol headers, version negotiation,
request routing, or cache metadata.

Required work:

- Adopt the v2-supported Streamable HTTP handler and validate protocol-version and
  request-identification headers required by the selected SDK/API.
- Maintain stdio as a first-class transport through the v2-supported stdio runner.
- Define one endpoint path policy, response error mapping, CORS/auth integration
  boundaries, and observability that do not inspect private server objects.
- Emit required cache hints (`ttlMs` and cache scope) for cacheable modern responses,
  or mark responses non-cacheable where correct.

### 5. MCP surface adapters

Tools, prompts, and resources are public protocol surfaces, but their implementations
currently receive FastMCP `Context` objects and return JSON-encoded internal results.

Required work:

- Refactor decorators and handlers to receive `RequestContext` rather than FastMCP
  context objects.
- Map internal `Result` and rendered content to SDK-native tool, prompt, and resource
  results while preserving existing `instruction`, `additional_agent_instructions`,
  and display semantics.
- Route `guide://` URI extraction through the new resource request adapter.
- Preserve schema descriptions and tool/prompt names unless a public compatibility
  decision says otherwise.

### 6. Background and project-scoped work

`TaskManager` uses process-local timers and queued instructions that presently assume
a current session is available when the next tool or prompt runs.

Required work:

- Split process-wide services from per-project/per-interaction state.
- Key pending instructions, cached render context, and project task ownership by an
  explicit context identity rather than an ambient MCP session object.
- Define delivery semantics when a background event occurs without a subsequent
  request: queue only to a valid state owner, expire safely, and never deliver to a
  different project/client.
- Ensure project switches and configuration updates remain serialized and cleanup
  remains cancellation-safe under the new ownership model.

## Recommended Implementation Sequence

1. Pin and evaluate compatible v2 SDK/FastMCP versions in an isolated compatibility
   spike, using the local schema snapshot as the acceptance reference.
2. Establish modern protocol contract tests for discovery, stdio, and Streamable HTTP
   before replacing production entry points.
3. Introduce the request-context adapter and migrate session/project resolution,
   including explicit state round-trip and no-project behavior.
4. Rebuild server/transport bootstrapping and remove private handler monkeypatches.
5. Migrate tools, prompts, resources, result conversion, rendering, and task-manager
   delivery in slices behind the new adapter.
6. Validate modern interoperability, concurrency/isolation, state tampering/expiry,
   project switching, cache metadata, and regression behavior across both transports.
7. Make any legacy support opt-in, time-bounded, documented, and covered by a
   dedicated compatibility suite; otherwise remove it before release.

## Compatibility Decisions Still Needed

- Which exact Python MCP and FastMCP releases provide complete support for protocol
  revision `2026-07-28`?
- Is legacy protocol support required for a transition, and what published end date
  applies if it is?
- What authenticated principal is available in each deployment mode to bind signed
  request state safely, especially stdio?
- Which results are safely cacheable, and what TTL/scope is correct for rendered
  content, project configuration, and guide resources?
- Which server-to-client features are actually used by supported clients and need
  multi-round-trip replacement rather than retirement?
