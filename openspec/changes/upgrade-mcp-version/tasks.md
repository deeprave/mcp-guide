## 1. Protocol Baseline and Dependency Selection

- [x] 1.1 Create protocol fixtures from the checked-in `2026-07-28` schema for discovery, tool, prompt, resource, request-state, stdio, and Streamable HTTP flows, plus retained legacy-client flows.
- [x] 1.2 Evaluate FastMCP 4 public APIs against those fixtures; record the selected beta version, dual-protocol entry points, and modern request/session-state configuration.
- [x] 1.3 Define the negotiated dual-protocol policy: serve `2026-07-28` and retained handshake-era clients from FastMCP 4, with explicit application-state ownership.
- [x] 1.4 Add dependency constraints and lockfile updates only after the compatibility spike demonstrates the selected APIs.

## 2. Request Context and State Boundary

- [x] 2.1 Define framework-neutral request-context, response-metadata, owner-key, root-identity, active-configuration-project, `GuideRuntime`, and context-owned `Session` types.
- [x] 2.2 Implement extraction of negotiated revision, request identity, and client/agent metadata through FastMCP public APIs; resolve both legacy and modern interaction state through `GuideRuntime`; remove roots extraction.
- [x] 2.3 Implement and document FastMCP 4 request/session-state ownership, expiry, validation, and isolation for modern interactions.
- [x] 2.4 Add unit tests for modern and legacy context extraction, missing project context, interaction-owner isolation, and negotiated protocol behavior.
- [x] 2.5 Remove server-PWD project inference from remote request resolution while retaining explicit project selection behavior.

## 3. Server and Transport Entry Points

- [x] 3.1 Refactor server construction into a side-effect-free FastMCP 4 surface and explicit `GuideRuntime` start/stop lifecycle, replacing the `GuideMCP` subclass/private startup-handler contract while retaining all current process initialization.
- [x] 3.2 Replace stdio startup with the FastMCP 4 runner; create isolated context-owned Sessions (containing TaskManagers) and add modern and legacy interoperability/lifecycle tests.
- [x] 3.3 Migrate Streamable HTTP to the FastMCP 4 handler; retain the Starlette/Uvicorn host wrapper only where its public API remains needed and test both negotiated eras.
- [x] 3.4 Preserve current response semantics and add modern/legacy protocol tests, including request-state and cache-hint metadata where supported.
- [x] 3.5 Remove private FastMCP/MCP lifecycle assumptions from server startup and transport code.

## 4. Project Context and Lifecycle Migration

- [x] 4.1 Make GuideRuntime the explicit global-state owner: lift the existing class-level `Session._ConfigManager` singleton into a plainly named `GuideRuntime.ConfigManager`, created at runtime startup. Give it the one persistence lock, complete validated configuration snapshot, and one configuration-file watchdog; update/replace and diff that snapshot on both writes and detected external changes, suppress duplicate publications, and remove per-Session construction/reconfiguration/watching while keeping Session as the only runtime application-facing route to configuration operations. Resolve docroot once into GuideRuntime at startup and reject/defer every runtime attempt to change its effective value until restart.
- [x] 4.2 Replace bootstrap and active-session correctness paths with explicit request-context propagation.
- [x] 4.3 Remove the weak registry keyed by `MiddlewareServerSession`, the private `_handle_message` roots-change monkeypatch, and all `roots/list` paths.
- [x] 4.4 Replace `set_project`'s public argument `name` with required absolute client filesystem `path`; derive root basename/hash from it, bind only an unbound interaction through validated state, reject every later `set_project` call, and preserve `switch_project(name)` as independent active-configuration selection keyed by `(name, bound_root_hash)`.
- [x] 4.5 Make configuration resolution strict: accept only a generated `<project-name>-<hash>` key and stored hash matching the bound root hash; remove all name-only fallbacks and all legacy migration behavior, ignoring malformed, hashless, or mismatched entries and creating/selecting only the correct key. Permit an exact hashless raw key solely as an explicit `clone_project` source recovery path, falling back from an unhashed source name to a unique strict hash-suffixed match and reporting competing hash-suffixed matches. Immediately publish global/project configuration changes through the shared ConfigManager, and add concurrency/project-selection coverage for independent interactions, unselected roots, rejected repeated set_project calls, name-based configuration switching without root mutation, ignored malformed/missing/mismatched keys, clone recovery precedence, and external configuration changes.

## 5. MCP Surface Adaptation

- [x] 5.1 Implement the common adapter from internal `Result` and rendered content to SDK-native tool, prompt, and resource responses.
- [x] 5.2 Migrate tool registration and decorators to inject request context and stop JSON-string serialization at the SDK boundary, including the breaking `set_project(path)` schema and `clone_project(from_project)` current-target-only contract.
- [x] 5.3 Migrate prompt registration and rendering to request context and the common result adapter.
- [x] 5.4 Migrate guide resource and command URI handling to public FastMCP 4 request-scoped URI extraction, including the optional RFC 6570 `session_id` query variable resolved by the same Session boundary as tool arguments.
- [x] 5.5 Add regression tests proving embedded instructions, `additional_agent_instructions`, errors, and dispositions survive each public MCP surface, plus current-target-only cloning, exact hash-suffixed source-key precedence, and ambiguous source-name errors listing matching keys.

## 6. Task Manager and Background Work

- [x] 6.1 Replace the process-global TaskManager with a TaskManager instance contained by each context-owned Session. Create and tear it down with its Session; it owns pending instructions, acknowledgements, caches, timers, and project-scoped tasks. Use one Session for stdio and partition HTTP Sessions by explicit owner/project keys.
- [x] 6.2 Refactor task lifecycle APIs to receive the context-owned Session/request context rather than reading an ambient MCP session or process-global task manager; on configuration publication, invoke each affected Session's listener lifecycle so its TaskManager refreshes flags and startup/shutdown/interception state.
- [x] 6.3 Retire roots-dependent flows and redesign any remaining server-to-client flows to use supported multi-round-trip input where needed, with documented behavior.
- [x] 6.4 Define expiry and cleanup behavior for undeliverable instructions and invalid interaction state.
- [x] 6.5 Add task-manager tests for concurrent clients/projects, explicit project selection and rejected reselection, background delivery, expiry, cleanup, and cancellation.

## 7. Documentation

- [x] 7.1 Document the supported protocol revisions, client migration instructions, HTTP requirements, state behavior, and any legacy bridge end date.
- [x] 7.2 Document tool-contract changes, operational downgrade/reconnect behavior, and configuration compatibility.
