## 1. Listener Protocol Update
- [x] 1.1 Define `SessionListener` protocol with `on_project_changed` and `on_config_changed`
- [x] 1.2 Update existing listener implementations

## 2. Instance-Level Listeners
- [x] 2.1 Move `_listeners` from `ClassVar[list]` to `__init__` instance attribute
- [x] 2.2 Convert `add_listener`, `remove_listener`, `clear_listeners` from classmethods to instance methods
- [x] 2.3 Call `on_project_changed` from `switch_project()` with old/new project names
- [x] 2.4 Fire `on_project_changed("", project_name)` on initial session creation

## 3. Per-Session Template Cache
- [x] 3.1 Remove module-level `_template_context_cache` global from `render/cache.py`
- [x] 3.2 Make `TemplateContextCache` hold its cache as instance state (`self._cache`)
- [x] 3.3 Add `Session.template_cache` property (lazy creation, auto-registers as listener)
- [x] 3.4 Update module-level functions to route through current session's cache

## 4. Fix StartupInstructionListener
- [x] 4.1 Remove shared `_processed_sessions` set
- [x] 4.2 Listen only on `on_project_changed` (project-scoped, not session-scoped)

## 5. Registration and Wiring
- [x] 5.1 Move listener registration into `get_or_create_session()`
- [x] 5.2 Remove class-level registration from `server.py`
- [x] 5.3 Update test fixtures to use instance-level API
