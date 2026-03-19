# Change: Refactor Session Listeners to Instance-Level

## Why

Session listeners are currently class-level (`ClassVar[list]`), shared across all Session
instances. The template context cache is a module-level global. This causes bugs in HTTP
transport with multiple concurrent clients:

1. **Template cache thrashing** — one client's project switch invalidates the cache for all
   clients, since `_template_context_cache` is a single module global.
2. **StartupInstructionListener dedup broken** — deduplicates by project name in a shared set,
   so a second client connecting to the same project never receives startup instructions.
3. **Cross-session notification** — `_notify_listeners()` fires for all registered listeners
   regardless of which session triggered the change.

Sessions now have a 1:1 relationship with agents and persist for the connection lifetime.
This makes instance-level listeners the correct design — each session owns its listeners
and its own cache state, with no shared mutable globals.

This refactor is a prerequisite for `add-roots-change-handler`, which calls `switch_project()`
and relies on correct per-session notification.

## What Changes

- Move `_listeners` from `ClassVar[list]` to instance attribute on Session
- Move `add_listener`, `remove_listener`, `clear_listeners` from `@classmethod` to instance methods
- Add `on_project_changed(session, old_project, new_project)` to `SessionListener` protocol
- Call `on_project_changed` from `switch_project()` with old and new project names
- Make `TemplateContextCache` instance-per-session (not module-level singleton)
- Remove module-level `_template_context_cache` global; cache lives on the instance
- Register listeners during session creation, not as a class-level side effect
- Fix `StartupInstructionListener` to track per-session state (not shared set)

## Impact

- Affected specs: `session-management` (MODIFIED)
- Affected code:
  - `src/mcp_guide/session.py` — listeners become instance-level
  - `src/mcp_guide/session_listener.py` — add `on_project_changed` to protocol
  - `src/mcp_guide/render/cache.py` — `TemplateContextCache` becomes per-session, remove global
  - `src/mcp_guide/startup_listener.py` — per-session dedup instead of shared set
  - `src/mcp_guide/server.py` — listener registration moves to session creation
  - Tests — update listener registration patterns
- **BREAKING**: None externally. Internal API change — `Session.add_listener()` becomes
  `session.add_listener()` (instance method). No public MCP tool changes.
