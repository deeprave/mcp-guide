## Context

`mcp-guide` currently exposes a FastMCP server through custom stdio and HTTP
wrappers. Its application state assumes a durable client connection: a task-local
`Session`, a weak registry keyed by `MiddlewareServerSession`, bootstrap context
variables, and a `server.py` monkeypatch of FastMCP's private message handler allow
the server to request roots and react to roots notifications. The repository also has
many direct `fastmcp.Context` parameters across tools, prompts, and resources, and a
single process-global `TaskManager` whose mutable queues and project tasks are not
partitioned by client or project.

MCP protocol revision `2026-07-28` and its v2 SDK model make request negotiation,
request context, and multi-round-trip state explicit. The authoritative local schema
copy is in [`../../std/mcp-schema-2026-07-28.ts`](../../std/mcp-schema-2026-07-28.ts)
and the detailed repository impact analysis is in `analysis.md`. This is an
architectural migration, not a package-version-only change.

## Goals / Non-Goals

**Goals:**

- Support MCP protocol revision `2026-07-28` through FastMCP 4's public API, with
  negotiated modern and retained legacy compatibility.
- Introduce a framework-neutral request context that makes project resolution,
  client metadata, and state ownership explicit.
- Eliminate private MCP/FastMCP monkeypatches and connection-object dependencies.
- Preserve guide tools, prompts, resources, rendering semantics, and project safety
  across stdio and Streamable HTTP. Existing functional behaviour is the baseline;
  any protocol-imposed exception requires an explicit compatibility decision.
- Make stateful interactions, background instruction delivery, and project-scoped
  task lifecycle safe under concurrent and stateless requests.

**Non-Goals:**

- Redesign guide domain behavior, project configuration format, templates, or the
  workflow model except where context/state ownership requires it.
- Promise support for every historical MCP protocol revision.
- Add new product capabilities unrelated to the MCP v2 migration.
- Implement this migration in this proposal phase.

## Decisions

### 1. Target the date-stamped protocol revision, not a fictitious wire `2.0.0`

The compatibility target is MCP `2026-07-28`; "v2" identifies the SDK migration
line. The server will negotiate supported revisions and reject unsupported requests
through the selected SDK's standard mechanism.

**Rationale:** the upstream schema defines date-stamped protocol revisions. Treating
`2.0.0` as a wire value would create invalid negotiation behavior.

**Alternative considered:** only increase FastMCP's version and retain current
initialization assumptions. Rejected because the private connection/session coupling
is the primary incompatibility.

### 2. Place a framework-neutral request-context adapter at the protocol boundary

Introduce an application `RequestContext` assembled by a transport/SDK adapter. It
will expose: negotiated revision, request identity, client/agent data, selected project
identity, safe request-state access, and a narrowly defined response metadata
builder. Application services will not receive raw SDK contexts. A transitional
registration facade may accept the SDK context only at the decorator boundary and
immediately construct the application context; this permits the many existing
handlers to migrate in slices without retaining SDK-specific correctness paths.

**Rationale:** this confines SDK API churn to a small adapter and lets tools,
resources, rendering, and session services be tested without a live transport.

**Alternative considered:** change all callers directly to the new FastMCP context.
Rejected because the current code already has many FastMCP-context call sites and
would remain tightly coupled to a framework-specific request shape.

### 3. Replace connection-bound sessions with explicit durable and interaction state

Project configuration remains durable storage. Request-specific data lives in
`RequestContext`. Cross-request interaction state, only when needed, is serialized
through the SDK's request-state facility, using its `RequestStateSecurity` support
with stable deployment keys. Application payloads remain versioned, expiry-bound,
and bound to the available principal/client scope and the request context they
authorize; server-side indirection is permitted for large or sensitive values.

An explicit state owner key will select a context-owned Guide `Session` held by the
application runtime. The Session contains its own non-global TaskManager instance,
which owns pending instructions, rendering caches, timers, and project-scoped task
state. Session and TaskManager are created and torn down together. Under stdio, the
normal one-agent process resolves one Guide Session through the same registry lookup,
preserving current single-agent *behaviour* without preserving a global TaskManager;
it does not weaken isolation if more than one Session is ever present. Under HTTP, it
creates or restores one Session per validated owner. `GuideRuntime` is the
process-global Guide state: it holds the Session registry, lifecycle, shared
ConfigManager, the startup-resolved shared docroot, service factories, and coordination locks. It may coordinate cleanup,
but it may not contain mutable agent, active-configuration selection, rendering, or
task state, nor infer a recipient from a `ContextVar` or a raw SDK connection object.

Durable Guide configuration is the intentional shared-state exception. The existing
class-level `Session._ConfigManager` is a process singleton in all but name; v2 moves
that responsibility out of `Session` and into `GuideRuntime.ConfigManager`.
That manager owns the configuration-file resource, including its lock, one complete
validated configuration snapshot/cache, persistence, its watchdog, and change
publication. It updates the complete cached snapshot as part of a successful write
before publishing its diff. Its single watchdog remains required: when any writer
(another Guide runtime/session or an external process) changes the configuration file,
it reloads the complete snapshot under the same coordination discipline, compares it
with the prior snapshot, atomically replaces the cache, and publishes the resulting
global and exact-project changes. A successful configuration write
must publish immediately within that runtime after persistence: global feature-flag
changes go to every Session; a project-configuration change goes to every Session
whose active configuration has the same exact `(name, root_hash)` identity. The
ConfigManager owns one watcher for configuration-file changes and fans detected
changes out by the same rules. A watcher event that observes the already-cached
snapshot SHALL not cause a duplicate publication. Sessions remain isolated in how they react, but they do
not retain stale configuration. A Session receives the runtime-owned service (or a
read-only configuration view) through construction/request context; it SHALL NOT own,
reconfigure, or watch the shared configuration file. Runtime application code SHALL
obtain configuration operations only through a Session; it SHALL NOT create another
ConfigManager or use the runtime-owned manager as a general-purpose service locator.

Docroot is likewise a shared runtime resource, not Session configuration. Runtime
startup resolves it once and stores the effective docroot on GuideRuntime. It is
immutable for that runtime's lifetime: no Session operation, in-process configuration
write, or watchdog publication may alter it. If a configuration-file change contains a
different docroot, ConfigManager may cache that persisted value for a future runtime,
but the running GuideRuntime continues using its startup-resolved docroot; restart is
required to adopt it.

Each affected Session dispatches the existing Session-listener lifecycle locally. Its
contained TaskManager invalidates derived flags and performs the appropriate task
startup, shutdown, or event-interception refresh for the new configuration. This is
not a shared TaskManager operation: the shared service publishes a change, and each
Session updates its own runtime state.

FastMCP is the protocol dispatcher, not the owner of Guide Sessions. For each request,
its public context supplies transport metadata and validated request state to
the request adapter. The adapter derives a Session key from the verified owner and
interaction state, then asks `GuideRuntime`'s Session registry to resolve or create
the corresponding unbound Guide Session. In stdio the registry resolves its sole agent
Session; in HTTP it resolves the owner-partitioned Session. Client display metadata
such as name/version is not a Session key. The resulting Session is placed in the
application `RequestContext` for the handler and any background work it initiates.

MCP has no parent/subagent session model. A subagent is therefore a separate Session
registry owner by default, whether it has its own MCP server process or connects to a
shared remote server. Subagents may bind the same root and use the same durable Guide
configuration, but they do not share mutable Session state such as TaskManager queues,
timers, caches, or active configuration selection. Deliberate parent-to-subagent state
sharing requires an explicitly issued, validated descendant Session state; it is never
inferred from client name, root, or process ancestry.

**Rationale:** it meets stateless execution while preventing instruction or project
data from crossing clients or projects.

**Alternative considered:** retain a server-memory map keyed by transport session ID.
Rejected as the primary model because it cannot satisfy stateless HTTP requests,
multi-process deployment, or protocol request-state integrity requirements.

### 4. Separate pure server construction from application-runtime startup

FastMCP construction is not server startup. The migration will introduce an
explicit `GuideRuntime` application object, constructed from `ServerConfig`, which
owns process-wide initialization and shutdown. Its lifecycle is:

1. construct the runtime and configure process services that need configuration;
2. construct and register the public FastMCP surface without accepting requests;
3. start the runtime exactly once before the selected transport accepts requests;
4. bind the owner’s Guide Session while dispatching each request; and
5. stop transport, Guide Sessions (including their task managers), watchers, timers,
   and process services in a
   defined shutdown order.

Registration of tools, prompts, resources, and task classes remains deterministic and
idempotent. Startup must retain the current initialization effects (logging,
configuration overrides, task registration, and cleanup) without using FastMCP
construction side effects or `GuideMCP.on_init`.

**Rationale:** the current `GuideMCP` exists chiefly to obtain FastMCP lifecycle hooks
and to carry session-oriented conveniences. Those responsibilities belong to an
explicit application runtime, while FastMCP remains a protocol surface
that can be built and tested before it is run.

**Alternative considered:** preserve `GuideMCP` as a subclass or replace it with a
thin FastMCP subclass. Rejected unless the compatibility spike identifies a
public FastMCP extension point that genuinely needs it; subclassing solely to recover old
construction side effects would retain the wrong lifecycle model.

### 5. Make project binding an explicit, one-interaction selection

Project binding occurs when the agent determines its root and invokes Guide's explicit
project-selection path with an absolute client filesystem `path`. The public argument
is `path`, not `name`: the project display name is derived from the path basename and
the path is used for root identity/hash resolution. This root binding is stored in
validated interaction state. An interaction has one root: selecting a different path
requires a new interaction/session rather than mutating the active root. `set_project`
is valid only while the interaction is unbound; every later call is rejected,
including a repeat of the same canonical path.

This does **not** replace `switch_project(name)`. That operation remains the explicit
selection of the active Guide configuration project and may change configuration within
the same root-bound interaction. It accepts a configuration name, never claims to
identify the client filesystem root, and must remain available as an independent
configuration operation. Configuration identity is the pair of its selected `name`
and the bound root's path hash. Therefore `set_project(path)` selects the default
configuration name from `path`'s basename using that hash, while
`switch_project(name)` selects a different configuration name using the **same** bound
root hash. This retains distinct configurations with the same name at different roots
without passing a full path to `switch_project`.

Configuration resolution is strict: the generated `(name, bound_root_hash)` key and
the stored configuration hash must both match. A name-only lookup, a matching name
with a different hash, a matching name with no hash, or a malformed key are all
ignored; they must not silently select another root's configuration. Guide provides no
legacy configuration migration. Resolution selects or creates only the correct
`<project-name>-<hash>` key for the bound root.

`clone_project` is the sole explicit recovery exception. When its source argument
has no hash suffix, it first checks for an exact raw hashless configuration key, then
falls back to a unique strict hash-suffixed entry with that display name. It only
copies content into the already bound, correctly hashed target; it neither loads nor
rewrites the legacy source as an active configuration. This is a user-invoked recovery
operation, not legacy configuration support or automatic migration.

**Rationale:** the `<project-name>-<hash>` format has been established for many
released versions. Retaining a compatibility path for older or malformed entries would
reintroduce ambiguous root selection for comparatively little benefit. Legacy entries
remain ignored in ordinary operation; an explicit clone into a bound current project
is available when retaining their content is useful. This is an intentional
compatibility decision, not automatic migration.

The server will remove its private `roots/list_changed` handler and all `roots/list`
requests. Roots have proven unreliable in clients and are deprecated by the current
protocol; they are not a compatibility path for this migration. For a stdio process
started by a CLI agent, Guide MAY use a valid absolute inherited `PWD` as the
client-launch project path and bind the new interaction immediately. This is a
stdio-only bootstrap rule; HTTP and other remote transports SHALL NOT use the server
process environment to infer a client's project.

**Rationale:** project choice is an agent decision, not discoverable server state. An
explicit one-interaction selection matches present agent practice and removes an
unreliable client capability and session-mutation race. The inherited-PWD shortcut
preserves the established CLI-agent behavior only when the client starts Guide from
the project directory; otherwise `set_project(path)` remains required. Requiring a
path for root binding prevents clients from treating a project name as sufficient
filesystem identity, while retaining the useful separate name-based configuration
selection feature.

**Alternative considered:** retain roots support through a public legacy SDK callback.
Rejected because clients have not reliably implemented it and it unnecessarily
preserves a server-initiated project-selection path.

### 6. Create one public result adapter for modern MCP content and metadata

Keep domain-level `Result` and rendered-content objects independent. A single adapter
will convert them to SDK-native tool, prompt, and resource responses, preserving
instruction dispositions and `additional_agent_instructions`. It will attach cache
hints only when the response is actually safe to cache, with conservative defaults.

**Rationale:** stringifying result JSON before handing it to FastMCP hides protocol
semantics and makes cache metadata and multi-round-trip state difficult to express.

**Alternative considered:** preserve JSON-string responses and layer metadata in
templates. Rejected because protocol metadata belongs in the protocol result, not
rendered user content.

### 6a. Carry explicit Session identity in native Guide resource URIs

`resources/read` does not accept arbitrary tool arguments. Guide's resource templates
therefore advertise FastMCP's supported RFC 6570 query variable:
`guide://{collection}/{document}{?session_id}` and
`guide://_{command_path*}{?session_id}`. The resource adapter reads that value and
passes it through the same validation and Session-resolution boundary as a tool's
optional `session_id` argument. It is the FastMCP Session ID itself; Guide creates no
second identifier or state-bucket mapping.

This is required because Guide templates can condition rendering on Session state.
The `guide.read_resource` tool remains a useful compatibility shortcut for clients
that do not discover or expand resource templates, but it must produce the same
Session-sensitive result when supplied the same identifier. Retained handshake-era
resource reads that do not carry the query variable use public `ctx.session_id` as
their connection-scoped fallback. A modern request without the value remains unbound
unless it is a defined creation/bootstrap operation.

### 7. Use FastMCP 4's dual-era serving support, verified by a compatibility spike

FastMCP 4 documents one server surface that answers both legacy 2025 initialization
and modern 2026 requests. The first implementation task will verify that claim
against the checked-in schema and the guide surface, then record the selected version,
public FastMCP APIs, and an explicit supported-client policy
before the entry-point rewrite begins. It will not introduce a bespoke legacy bridge
unless the public SDK compatibility path demonstrably fails a required client.

**Rationale:** package releases may not align one-to-one with the standard and the
repository must avoid designing against an assumed API.

**Alternative considered:** pin an unverified dependency version in this proposal.
Rejected as premature and likely to produce a migration plan tied to non-existent or
incomplete APIs.

## Risks / Trade-offs

- **[SDK/API availability differs from the protocol]** -> Run the compatibility
  spike first; do not merge entry-point migration until required modern operations
  are exercised against the selected packages.
- **[State token replay or substitution]** -> Sign, expire, and bind state to the
  available principal and request authorisation scope; test tampering and replay.
- **[Explicit-selection migration]** -> Document that roots are no longer consulted;
  require project selection once per interaction and test the defined no-project and
  rejected-reselection behaviours.
- **[Instruction leakage or destructive project switch]** -> Replace the global
  TaskManager with Session-owned task state. Preserve present per-agent behaviour in
  stdio and partition HTTP Sessions by owner/project; add
  concurrency/isolation tests.
- **[Startup ordering regression]** -> Make runtime startup and shutdown explicit,
  idempotent, and covered by lifecycle tests before moving either transport.
- **[Legacy client disruption]** -> Exercise the SDK's documented dual-era serving
  path before release; publish the retained legacy revisions and remove only behaviour
  that lacks a public SDK compatibility mechanism.
- **[Large migration blast radius]** -> Migrate through an adapter with contract
  tests, preserving domain services until each transport surface is verified.

## Migration Plan

1. Add protocol fixtures, package compatibility spike, and a documented selected
   dependency/revision matrix. No legacy behavior is removed at this point.
2. Implement and test `GuideRuntime`, context-owned Guide Sessions (each containing
   a TaskManager), and the request-context boundary alongside current domain services.
3. Move stdio and Streamable HTTP to the v2-supported entry points and validate
   discovery, negotiation, errors, and response metadata.
4. Migrate tools, prompts, guide resources, result conversion, rendering context,
   and no-project behavior onto the adapter.
5. Migrate TaskManager delivery, cache ownership, and project lifecycle into
   Session-owned TaskManager instances; remove
   session registry/bootstrap state/private-handler code only after equivalent
   behavior is covered.
6. Run interoperability, security, concurrency, and full regression suites. Release
   with the documented SDK-supported legacy and modern revision policy; add a bespoke
   bridge only if the compatibility spike demonstrates an unmet required client.

Rollback: retain the prior released package version and configuration while the v2
release is staged. After persisted request-state formats are introduced, make them
versioned and ignore unknown versions safely so rollback does not deserialize v2
state as legacy state.

## Open Questions

- Which FastMCP 4 public APIs should Guide use for each stdio, Streamable HTTP,
  discovery, and request-state boundary?
- Which authentication/principal data is available in stdio and HTTP deployments for
  state-token binding, and what server-side state store is required?
- Which legacy client revisions must remain supported? The default is the SDK's
  built-in dual-era path, not a bespoke bridge.
- Does the compatibility spike reveal a public SDK lifecycle hook that requires a
  thin server extension, or can `GuideMCP` be removed entirely as expected?
- Which current uses of sampling, elicitation, and subscriptions are exercised in
  production clients?
- Which guide responses can safely declare cache metadata, and at what scope/TTL?
