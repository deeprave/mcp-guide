# Implementation Tasks

## 1. Session Listener Refactoring (BREAKING)
- [x] 1.1 Update `SessionListener` protocol signature:
  - [x] Change `on_session_changed(self, project_name: str)` to `on_session_changed(self, session: Session)`
  - [x] Change `on_config_changed(self, project_name: str)` to `on_config_changed(self, session: Session)`
- [x] 1.2 Make `Session._listeners` class-level (ClassVar)
- [x] 1.3 Update `Session._notify_listeners()` to pass `self` instead of `self.project_name`
- [x] 1.4 Update `Session._notify_config_changed()` to pass `self` instead of `self.project_name`
- [x] 1.5 Update `TemplateContextCache.on_session_changed()` to accept `Session` parameter
- [x] 1.6 Update `TemplateContextCache.on_config_changed()` to accept `Session` parameter
- [x] 1.7 Extract `project_name` from session in cache methods if needed

## 2. Feature Flag Definition
- [x] 2.1 Add `startup-instruction` to feature flag schema (string type, optional)
- [ ] 2.2 Document flag in feature flags documentation

## 3. Expression Validation
- [x] 3.1 Create expression parser to extract categories/collections
- [x] 3.2 Implement validation logic:
  - [x] Parse expression into components
  - [x] Validate each category exists in project
  - [x] Validate each collection exists in project
  - [x] Ignore patterns (validated at runtime by get_content)
- [x] 3.3 Add validation to flag setter (reject invalid expressions)
- [x] 3.4 Return clear error messages for invalid expressions

## 4. Startup Template
- [x] 4.1 Template `_startup.md` already exists in templates directory
- [x] 4.2 Has frontmatter: `requires-startup-instruction: true`
- [x] 4.3 Has frontmatter: `type: agent/instruction`
- [x] 4.4 Template content with `{{feature_flags.startup-instruction}}` variable
- [x] 4.5 Includes instruction to call `get_content("{{feature_flags.startup-instruction}}")`
- [x] 4.6 Includes confirmation requirement

## 5. Startup Instruction Listener
- [x] 5.1 Create `StartupInstructionListener` class implementing `SessionListener`
- [x] 5.2 Implement `on_session_changed(self, session: Session)`:
  - [x] Render `_startup.md` template for the session
  - [x] If content is non-blank, call `queue_instruction(content, priority=True)`
  - [x] Track processed sessions to avoid duplicates
- [x] 5.3 Implement `on_config_changed(self, session: Session)` (no-op or re-render if needed)
- [x] 5.4 Register listener at server startup in `create_server()`
- [x] 5.5 Remove old callback injection code from `server.py`
- [x] 5.6 Remove `handle_project_load()` function and related code

## 6. Template Rendering Support
- [x] 6.1 `requires-startup-instruction` directive already handled (generic requires-* system)
- [x] 6.2 Template filtered when flag not set or empty
- [x] 6.3 Flag value passed to template context via `feature_flags`
- [x] 6.4 Blank rendered content not queued

## 7. Instruction Queueing
- [x] 7.1 Add optional `priority: bool = False` parameter to `queue_instruction()` method
- [x] 7.2 When `priority=True`, insert instruction at front of queue (index 0)
- [x] 7.3 When `priority=False`, append to end of queue (existing behavior)

## 8. Testing
- [x] 8.1 Test listener refactoring:
  - [x] Verify class-level listener storage
  - [x] Verify all sessions notify same listeners
  - [x] Verify session passed to listener methods
- [ ] 8.2 Test with flag not set (template filtered, no instruction)
- [ ] 8.3 Test with empty flag (template filtered, no instruction)
- [ ] 8.4 Test with valid collection expression
- [ ] 8.5 Test with valid category expression
- [ ] 8.6 Test with valid category+pattern expression
- [ ] 8.7 Test with multiple expressions
- [ ] 8.8 Test validation rejects invalid categories
- [ ] 8.9 Test validation rejects invalid collections
- [ ] 8.10 Test template renders with flag value
- [ ] 8.11 Test instruction triggers on session creation
- [ ] 8.12 Test instruction triggers on session switch
- [ ] 8.13 Test instruction not duplicated per session
- [ ] 8.14 Test blank template content not queued

## 9. Documentation
- [ ] 9.1 Document `startup-instruction` flag in feature flags guide
- [ ] 9.2 Add examples of valid expressions
- [ ] 9.3 Document `_startup.md` template
- [ ] 9.4 Document validation behavior
- [ ] 9.5 Add troubleshooting section for common errors
- [ ] 9.6 Update all feature flag documentation to include `startup-instruction`
- [ ] 9.7 Document fire-and-forget behavior (queued, sent via Result, no acknowledgment)
- [ ] 9.8 Document highest-priority queueing behavior
- [ ] 9.9 Document session listener refactoring (breaking change)
