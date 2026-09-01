# MCP v2 Upgrade Analysis

## Target and Evidence

The target is MCP protocol revision `2026-07-28`. The local authoritative schema
snapshot is [`../../std/mcp-schema-2026-07-28.ts`](../../std/mcp-schema-2026-07-28.ts);
FastMCP 4.0.0b3 is the direct integration target. It builds on MCP SDK v2; neither
package version is a protocol version that clients negotiate.

The analysis uses FastMCP 4's upgrade guidance. It retains the separately maintained
framework and negotiates legacy 2025 initialization and modern 2026 requests from one
server. The repository previously resolved FastMCP 3.4.5 and MCP 1.28.1; the spike
now pins the FastMCP 4 beta and verifies its public API calls before entry-point work.

## Current Architecture Inventory

| Area | Current implementation | Upgrade implication |
| --- | --- | --- |
| Server entry point | `main.py` constructs `GuideMCP`, then immediately gives it to a transport; construction configures logging, task imports, registration, and FastMCP lifespan hooks. | Split pure FastMCP surface construction from explicit `GuideRuntime.start()`/shutdown, retaining every current initialization effect and the CLI transport contract. |
| Connection lifecycle | `server.py` patches private `_mcp_server._handle_message` and registers a low-level `RootsListChangedNotification` handler. | Remove the private monkeypatch and all roots handling; roots are not a supported project-selection path. |
| Session ownership | `session.py` combines a task-local `ContextVar` with a `WeakKeyDictionary` keyed by FastMCP `MiddlewareServerSession`. Its nested `Session._ConfigManager` is in fact a class-level process singleton, while sessions create watchers around it. | Make GuideRuntime the explicit global-state owner. Move the singleton responsibility to a plainly named `GuideRuntime.ConfigManager`, replace per-Session watchers with its one watcher, and keep Session as the only runtime application-facing route to configuration operations. Persist and immediately publish global/project configuration changes to affected Sessions; resolve docroot once at runtime startup and keep it immutable until restart. |
| Client context | `mcp_context.py` reads `ctx.session.client_params`, calls `ctx.session.list_roots()`, and uses bootstrap `ContextVar`s. | Build an adapter that extracts client metadata and request state from the modern request envelope. Remove roots extraction and bootstrap state. |
| Project selection | First root and, as a fallback, inherited `PWD` determine the project. The current `set_project` schema accepts only a `name`, although `Session.switch_project` accepts paths opportunistically. | For stdio CLI agents started from a project directory, retain valid inherited `PWD` as a one-time binding bootstrap. Otherwise make `set_project(path)` explicitly bind the client root and store it immutably in interaction state. Preserve `switch_project(name)` as a separate name-based active-configuration operation that does not identify or change the root. |
| Configuration cloning | `clone_project` accepts `from_project` and optional `to_project`, each resolved by key or relaxed name matching; it can create or write a target unrelated to the active interaction. | Restrict cloning to one source selector and the current active configuration target. Resolve an exact hash-suffixed source key first, otherwise a unique display-name match; ambiguity must return the matching keys rather than selecting an arbitrary source. |
| Resources | `resources.py` reads `ctx.request_context.request.params.uri`. | Keep URI access behind the new request-context adapter so guide resources are independent of a FastMCP private object shape. |
| Results | Tool, prompt, and resource wrappers serialize internal `Result` values to JSON strings before FastMCP emits them. | Rework the boundary to produce SDK-native result/content structures, including protocol metadata and cache directives where applicable. |
| Task manager | One process-local `TaskManager` owns unpartitioned timers, instruction queues, cache, and project-scoped task instances; project changes clear all of them. | Replace the global manager with a TaskManager instance contained by each context-owned Guide Session and reached through `RequestContext`. GuideRuntime keeps only the Session registry and process coordination; stdio normally has one Session per agent process, while HTTP partitions Sessions by validated owner/project. |

## Protocol Capability Changes and Required Work

### 1. Discovery, negotiation, and stateless execution

The modern protocol uses `server/discover` and version negotiation rather than
assuming a persistent legacy initialization handshake. The SDK documents a dual-era
server surface: modern requests are self-contained, while legacy initialization may
remain supported. The server must declare and test its supported-revision policy,
rather than implement a second transport or bespoke bridge by default.

Required work:

- Add a protocol adapter that accepts the modern request envelope and exposes only
  stable application-facing context.
- Rebuild the server entry point around FastMCP 4's public factory/handler API.
- Establish an explicit application-runtime lifecycle. FastMCP construction must
  have no request-acceptance or client-state side effect; `GuideRuntime.start()` runs
  process initialization once before the transport accepts requests.
- Remove use of private FastMCP/MCP server attributes, `MiddlewareServerSession`, and
  roots APIs.
- Exercise the SDK's documented dual-era behaviour with the required legacy clients
  and document the retained revision policy. A separate bridge is an exception only
  when that public compatibility path fails a required client.

### 2. Request context and state

The legacy design assumes that a client connection carries roots, client parameters,
and mutable `Session` state. The migration removes roots entirely: agents explicitly
select a project once they have chosen a root. Modern multi-round-trip interactions
carry FastMCP's minted `session_id`, which selects the resulting in-memory Guide
Session while the MCP server remains running.

Required work:

- Introduce a framework-neutral `RequestContext` carrying protocol revision,
  authenticated client identity (when provided), agent/client metadata, selected
  project, resolved context-owned Guide Session, and request method/parameters.
- Use the public FastMCP request context only to derive the verified owner and
  interaction-state inputs. `GuideRuntime` SHALL look up or create the corresponding
  Guide Session in its Session registry; neither FastMCP nor a raw SDK connection
  object owns application state. Client name/version metadata is display-only and is
  not a Session key.
- Treat subagents as independent Session owners by default. They may use the same
  durable configuration when bound to the same root, but shall not share mutable
  Session/TaskManager state.
- Make durable configuration explicitly shared: GuideRuntime's ConfigManager owns
  persistence and one external-change watcher. After a successful
  write it immediately publishes global feature-flag changes to all Sessions and
  exact project-configuration changes to all Sessions using `(name, root_hash)`.
  Each recipient invokes its own Session listeners and TaskManager refresh; no Session
  may continue with a stale in-memory configuration snapshot.
- Replace bootstrap and active-session `ContextVar` state with explicit arguments at
  application boundaries. Context variables may remain as tightly scoped convenience
  bindings, but not as the source of cross-request identity or correctness.
- Use FastMCP's minted, principal-validated `session_id` for `set_project` and other
  modern multi-round-trip interactions. Do not persist Guide Session state across an
  MCP server restart; only project configuration remains durable.
- Reject an unknown FastMCP session ID and do not create a replacement Guide Session
  for it.
- Define a predictable no-project result until the agent explicitly selects a
  project, except that a stdio CLI process may bind once from valid inherited `PWD`.
  Never fall back to roots or server `PWD` for a remote client.

### 3. Explicit project selection replaces roots

The existing roots-change path depends on a server-initiated `list_roots()` request
after a `roots/list_changed` notification. It has not been reliably implemented by
clients and is deprecated in `2026-07-28`. Project selection instead happens when an
agent chooses a root and calls the explicit Guide selection operation with its absolute
filesystem path.

Required work:

- Remove the patched roots-notification handler, all `roots/list` calls, and roots
  extraction from the request-context path.
- Bind the interaction to the root selected by the agent; reject a different root path
  in the same interaction and direct it to begin a new interaction.
- Replace the public project-selection argument `name` with required absolute `path`.
  Derive the display name from the basename and use the path to resolve the project
  hash; do not infer or reconstruct a client root from a name.
- Preserve `switch_project(name)` as a separate active-configuration operation. It
  must not change the interaction's bound root or be used to infer one. It resolves
  configuration identity from `(name, bound_root_hash)`, so the same name remains
  reusable at different filesystem roots.
- Remove `_load_existing_project()`'s name-only fallback. A configuration is eligible
  only when both its generated key and stored hash equal the interaction's bound-root
  hash. A missing or mismatched hash is a miss, never permission to select by name.
- Treat malformed, hashless, and mismatched configuration entries as ignored data, not
  lookup candidates. No compatibility migration is provided; normal resolution
  selects or creates only the correct `<project-name>-<hash>` key. The sole exception
  is `clone_project`: after strict name lookup fails, it may recover an exact raw
  hashless YAML key as an explicit source. That format is already long-established,
  and fresh configuration is an acceptable outcome for an ignored older entry outside
  this clone recovery path; this is deliberate rather than an unaddressed migration gap.
- Remove `clone_project`'s `to_project` argument and all temporary-session/noncurrent
  target paths. It must load the root-bound interaction's active configuration as the
  target and save only to that exact key/hash.
- Replace any needed client input flow with v2 multi-round-trip `inputRequired`
  behaviour rather than server-originated JSON-RPC requests.
- Audit sampling, elicitation, and resource subscription use before coding;
  any currently unsupported server-to-client behavior must be either redesigned or
  explicitly retired with migration guidance.

### 4. Transport and HTTP semantics

The existing HTTP wrapper delegates to FastMCP's Streamable HTTP application but has
no application-level policy for modern protocol headers, version negotiation,
request routing, or cache metadata.

Required work:

- Adopt the FastMCP 4 Streamable HTTP handler and validate the framework-managed
  protocol-version and request-identification behaviour. Retain the Starlette/Uvicorn
  host wrapper only when it remains a public, necessary integration point.
- Maintain stdio as a first-class transport through the FastMCP 4 stdio runner.
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

- Split process-wide services from Guide Session state. Replace—not port—the global
  TaskManager with an instance created, owned, and torn down by each Session. Preserve
  existing one-agent *behaviour* for stdio by creating one Guide Session.
- Key pending instructions, cached render context, timers, and project task ownership
  by an explicit context identity rather than an ambient MCP session object.
- Define delivery semantics when a background event occurs without a subsequent
  request: queue only to a valid state owner, expire safely, and never deliver to a
  different project/client.
- Ensure initial project binding and configuration updates remain serialized and
  cleanup remains cancellation-safe under the new ownership model.

## Recommended Implementation Sequence

1. Pin and evaluate the public Python MCP SDK v2 in an isolated compatibility spike,
   using the local schema snapshot as the acceptance reference.
2. Establish modern protocol contract tests for discovery, stdio, and Streamable HTTP
   before replacing production entry points.
3. Introduce the request-context adapter and migrate session/project resolution,
   including explicit state round-trip and no-project behavior.
4. Rebuild server/transport bootstrapping and remove private handler monkeypatches.
5. Migrate tools, prompts, resources, result conversion, rendering, and task-manager
   delivery in slices behind the new adapter.
6. Validate modern interoperability, concurrency/isolation, state tampering/expiry,
   explicit project selection, cache metadata, and regression behavior across both
   transports.
7. Document and cover the SDK-supported legacy policy with a dedicated compatibility
   suite; create a bespoke bridge only for a demonstrated required-client gap.

## Compatibility Decisions Still Needed

- Which exact Python MCP SDK v2 release provides the public APIs needed for protocol
  revision `2026-07-28`, including request state?
- Which legacy client revisions are required, and does each work through the SDK's
  dual-era surface without a bespoke bridge?
- What authenticated principal is available in each deployment mode to bind signed
  request state safely, especially stdio?
- Which results are safely cacheable, and what TTL/scope is correct for rendered
  content, project configuration, and guide resources?
- Which server-to-client features are actually used by supported clients and need
  multi-round-trip replacement rather than retirement?
