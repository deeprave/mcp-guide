## Context

See [proposal.md](proposal.md) for the motivation.  The FastMCP v4 migration
introduced a framework-neutral `RequestContext`, but it presently carries only
transport-level information.  Application handlers still receive raw FastMCP
context objects, resolve Sessions at multiple depths, and sometimes rely on
ambient `ContextVar` state.  A request can therefore lose its selected Session
or Project when it delegates to another handler.

`Project` is already the immutable representation of the selected project
configuration: it contains the categories, collections, flags, permissions,
exports, and configuration identity.  `Session` owns mutable interaction state
and replaces its active `Project` when configuration changes.  `GuideRuntime`
owns the private `ConfigManager`; the runtime must remain the public
application-facing façade for configuration operations.

## Goals / Non-Goals

**Goals:**

- Establish one resolved application context at each public MCP boundary and
  preserve it for every nested operation in that request.
- Make the active immutable `Project` directly available for reads while
  retaining `Session` ownership of mutable interaction and configuration work.
- Convert all application code paths to explicit context or Session propagation,
  so nested calls cannot silently select a replacement Session.
- Make unbound and missing-context states explicit and testable.

**Non-Goals:**

- Change MCP client-visible tool names, schemas, protocol negotiation, or
  persisted project configuration format.
- Retain a compatibility overload or ambient fallback for handlers that have
  not been migrated.
- Move `ConfigManager` into request contexts or expose it to production
  application code.
- Redesign response metadata, caching, or the client-facing session-id result
  contract; those remain the responsibility of their respective changes.

## Decisions

### Resolve once at the transport boundary

Public FastMCP decorators and resource/prompt adapters will be the only layer
that accepts a raw FastMCP context.  They will resolve the interaction and
construct a `RequestContext` before calling application code.  The resulting
context carries the client `session_id`, resolved `Session`, and, when bound,
root and project values. Protocol revision, request identity, owner keys, and
client metadata are consumed at the transport boundary and are not application
context fields.

Internal tool, prompt, resource, command, rendering, and result-processing
functions will accept this `RequestContext` (or an explicitly supplied
`Session` for independent background work).  Delegators pass the same instance
downward.  This is preferred to repeatedly passing an opaque `session_id`:
resolution and ownership validation occur once, and a nested call cannot omit
the identifier and silently resolve a different Session.

### Model active configuration as the actual Project

`RequestContext` will contain `session_id: str | None`, `session: Session`,
`root: RootIdentity | None`, and `project: Project | None`. The project reference is the Session's currently selected immutable Project,
exposed as a `RequestContext.project` property rather than a frozen snapshot.
An unbound interaction has neither root nor project.  Helpers that require a
bound project will reject that state clearly.  Configuration writes remain
Session operations: the Session performs the update and rebinds a replacement
immutable Project; later work in the request reads `RequestContext.project` and
therefore sees that replacement.  This preserves the existing immutability
model while making normal configuration reads direct.

### Keep application services behind context and runtime helpers

`RequestContext` will expose narrowly scoped helpers for state that a handler
needs during an invocation: project/root access, task-result processing, and
runtime-owned services.  These helpers delegate to its resolved Session or
`GuideRuntime` rather than re-discovering state from FastMCP.

`ConfigManager` remains private to `GuideRuntime`. `create_runtime()` is the
only site that constructs a `GuideRuntime` and installs it as the process
singleton. A second install while that slot is occupied raises.
`get_runtime()` returns that instance. `stop()` is the only
release, after which a later `create_runtime()` may install a successor.
Session keeps a private `_runtime` for
its own configuration-service use and does not publish it. Feature flags are
a runtime concern, not a Session concern. RequestContext never exposes the
configured document root. It captures a sync resolver once via
`get_docroot_resolver` (or asks the runtime to provide that function).
That function is sync so a hot path can resolve many document paths without
awaiting each join. Formatters receive that function rather than a
document-root path. The
runtime still returns the configured docroot for installer-state and
security-boundary checks; a missing user-supplied value uses the
config-adjacent default. Tests may access the manager only through explicit
test fixtures or construction seams.

### Remove ambient interaction ownership

Session and task-manager `ContextVar` ownership/access paths will be deleted
from production code.  Functions requiring interaction state must receive a
resolved `RequestContext` or explicit Session; otherwise they raise a clear
programming error.  This is preferred to a legacy fallback because a fallback
can make a missing propagation bug appear to work against a transient or wrong
Session.

Long-running background work that is intentionally outside a request will be
given an explicit Session at scheduling time.  It must not recreate ownership
from task-local state.

### Migrate all application surfaces as one coherent refactor

The migration will first establish the context constructor and runtime/session
interfaces, then convert decorators and public boundaries, then their delegated
handlers.  Tools, prompts, Guide resources, rendering, commands, template
access, and task-result processing must all be converted before the old access
paths are removed.  Direct unit tests must construct the application context or
pass an explicit Session; they will not use a production compatibility shim.

This deliberate all-surface conversion is preferred to a partial migration,
because mixed raw-context and application-context paths would preserve the
session-dropping failure mode that this change is intended to eliminate.

## Risks / Trade-offs

- [Broad internal signature changes can miss a rarely used delegator] → Search
  and convert every raw FastMCP context and Session lookup in production paths;
  add boundary-to-nested-operation tests for each public surface.
- [A stale Project reference is used after a configuration write] → Keep writes
  on Session and require callers to use the replacement Project returned by the
  write operation for subsequent work.
- [Unbound requests fail later than necessary] → Make project-dependent helpers
  validate binding at their entry point and cover both unbound and bound cases.
- [Background work outlives the request context] → Pass its owning Session
  explicitly when it is scheduled and keep no request-local ambient fallback.
- [Tests bypass the production adapter] → Provide explicit test constructors for
  resolved contexts and cover raw-boundary conversion separately.

## Migration Plan

1. Introduce the resolved context model, context construction boundary, direct
   Project reference, and runtime façade APIs with focused unit tests.
2. Convert public tool, prompt, and resource adapters and every delegated
   application path to accept and preserve the new context.
3. Convert task, rendering, command, and template helpers; update tests to use
   explicit contexts or Sessions.
4. Delete ambient Session/TaskManager access and `ActiveConfiguration`; verify
   no production handler accepts raw FastMCP context below its boundary.
5. Run focused concurrency/binding tests and the complete test suite.  The
   change is internal, so rollback is a normal source rollback if a release
   reveals an unconverted path; no persisted-data migration is required.
