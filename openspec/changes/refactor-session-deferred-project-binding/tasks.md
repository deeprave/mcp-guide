## 1. Session Deferred Binding Model
- [x] 1.1 Define a wrapper-based placeholder project representation that can safely occupy the session's non-optional project slot before binding
- [x] 1.2 Remove the requirement for `Session` construction with a real `Project` argument and initialize `self.__project` with the unbound wrapper
- [x] 1.3 Add explicit session APIs for binding or ensuring the real project is loaded from client context or explicit project name
- [x] 1.4 Identify all persistence and config-write boundaries that could receive the placeholder project
- [x] 1.5 Add guards so those boundaries either raise `NoProjectError` or intentionally no-op when invoked with the placeholder project
- [x] 1.6 Make `set_project(project_name)` bind an unbound session directly from the explicit project name instead of depending on prior auto-resolution
- [x] 1.7 Make placeholder project methods mimic safe real-project behavior where possible and raise explicit exceptions for operations that require a bound project
- [x] 1.8 Add tests covering unbound session creation, `Session` construction without a real project, guarded persistence paths, `set_project(...)` bootstrap, first bind from context, and repeated access after binding

## 2. Startup And Task Manager Lifecycle
- [x] 2.1 Split task manager startup into project-independent server init and project-bound initialization
- [x] 2.2 Ensure `@mcp.on_init()` no longer requires immediate project resolution
- [x] 2.3 Load resolved flags and other project-sensitive task manager state only after the real project is bound
- [x] 2.4 Add startup tests covering server init before any MCP context exists

## 3. Project-Bound Access Semantics
- [x] 3.1 Audit session, listener, and cache code paths that assume a real project and route them through the new binding guard
- [x] 3.2 Trigger binding from any context-bearing tool, prompt, or resource access that caches valid MCP context while the active project is unbound
- [x] 3.3 Reuse the existing project-load notification for the first real bind and suppress project-related events while unbound
- [x] 3.4 Ensure project resolution continues to rely on MCP roots, cached roots, or explicit project name, not server cwd
- [x] 3.5 Ensure explicit recovery paths such as `set_project(...)` remain usable when no prior project context exists

## 4. Tool Helpers and Unified Binding
- [x] 4.1 Add `get_session_and_project` helper in `tool_helpers.py`
- [x] 4.2 Refactor all tools to use `get_session_and_project` — fixes previously unguarded `get_project()` calls
- [x] 4.3 Extract `try_bind_from_roots` on Session — single bind point used by both `get_or_create_session` and `_handle_roots_changed`
- [x] 4.4 Remove `create_session` classmethod — `Session()` + `bind_project()` is the canonical path

## 5. Validation
- [x] 5.1 Run full test suite, lint, format, type checks
- [x] 5.2 Run `openspec validate refactor-session-deferred-project-binding --strict --no-interactive`
