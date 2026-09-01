## Why

The FastMCP v4 migration introduced `RequestContext`, but application handlers still
accept raw FastMCP contexts and repeatedly discover Sessions, projects, and runtime
services through transport-specific or ambient paths. This duplicates session
resolution, permits context drift within one request, and leaves the framework-neutral
boundary only partially implemented.

## What Changes

- Make a resolved application `RequestContext` the required context for internal
  tool, prompt, resource, rendering, command, and task-result operations; raw
  FastMCP context remains confined to the registration/transport boundary.
- Populate the context once with the resolved Guide `Session`, immutable bound-root
  identity, and the exact active immutable `Project` object selected by that Session.
  Remove the redundant `ActiveConfiguration` identity shape.
- Provide request-context helpers for contained application state, including
  project access, root access, task-result processing, and runtime-owned services,
  so handlers do not rediscover state through FastMCP or `ContextVar` lookups.
- Remove ambient Session/TaskManager `ContextVar` ownership fallbacks from production
  paths. Calls without a resolved request context or an explicitly supplied Session
  fail clearly rather than allocating or selecting replacement state.
- Keep mutable interaction operations on `Session`: binding, configuration updates,
  project switching, task queues, and caches. A configuration update returns and
  rebinds the replacement immutable `Project` rather than mutating the context's
  project reference.
- Keep `ConfigManager` private to `GuideRuntime`; expose required configuration
  operations through runtime or request-context facades rather than passing the
  manager through application code.

## Capabilities

### New Capabilities
- `request-context`: Framework-neutral, resolved application context carrying the
  Session, bound-root identity, active Project, and safe helper APIs.

### Modified Capabilities
- `session-management`: Replace ambient Session ownership/access with explicit
  request-context and Session propagation.
- `tool-infrastructure`: Adapt tool registration so raw FastMCP context is converted
  to a resolved application context before internal handler execution.
- `prompt-infrastructure`: Adapt prompt execution and command routing to consume the
  resolved application context.
- `mcp-resources-guide-scheme`: Adapt Guide resource and command URI handlers to
  consume the resolved application context.

## Impact

- Affected code: FastMCP decorators/adapters, `runtime.py`, `session.py`, command
  and rendering helpers, tool/prompt/resource handlers, task-result handling, and
  their tests.
- Internal handler signatures change from raw FastMCP context to `RequestContext`.
  The public MCP schemas, protocol negotiation, persisted project configuration, and
  client-visible tool names remain unchanged.
- This work is deliberately separate from the FastMCP v4 upgrade remediation: it
  completes the application-context architecture without changing the already-defined
  protocol migration scope.
