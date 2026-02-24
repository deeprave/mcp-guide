# Change: Add Startup Instruction Support

## Why
When a project loads or switches, agents need immediate access to critical startup instructions. Currently, there's no mechanism to automatically inject project-specific instructions that guide the agent's initial context and behaviour.

## What Changes

### Refactor Session Listener System
- **BREAKING**: Change `SessionListener` protocol to receive `Session` instead of `project_name`
  - `on_session_changed(self, session: Session) -> None`
  - `on_config_changed(self, session: Session) -> None`
- Make `_listeners` class-level in `Session` class (shared across all instances)
- Update existing `TemplateContextCache` listener to use new signature
- Register listeners once at server startup, not per-session

### Add `startup-instruction` Feature Flag
- **Type**: Project flag (string, optional)
- **Values**:
  - Not set / empty: No startup instruction
  - String: Content expression for `get_content()`
- **Format**: Any valid content expression:
  - Collection: `"guidelines"`
  - Category: `"docs"`
  - Category with pattern: `"docs/README*"`
  - Multiple: `"guidelines+conventions,docs/README*"`

### Add `StartupInstructionListener`
- Implements `SessionListener` protocol
- Responds to `on_session_changed()` events
- Renders `_startup.md` template when session loads
- Queues instruction with priority if content is non-blank

### Add `_startup.md` Template
- **Location**: Project templates directory
- **Frontmatter**: `requires-startup-instruction: true`
- **Purpose**: Renders startup instruction using flag value
- **Template variables**: Access to `{{feature_flags.startup-instruction}}` (flag value)
- **Filtering**: Only rendered if flag is set and non-empty

### Validation
When flag is set or changed:
- Parse expression to extract categories/collections
- Validate all categories and collections exist
- Patterns are NOT validated (handled by `get_content()`)
- Reject invalid expressions with clear error

### Trigger Points
Render and queue `_startup.md` when:
1. **Session created** (new project session)
2. **Session changed** (switch to different project)

### Implementation Design
Use class-level session listener pattern:
1. Create `StartupInstructionListener` implementing `SessionListener` protocol
2. Register listener once at server startup in `create_server()`
3. Listener responds to all session events (class-level, shared across instances)
4. On `on_session_changed()`, render `_startup.md` for that session
5. If rendered content is non-blank, call `queue_instruction(content, priority=True)`

### Rendering Flow
1. Session fires change event → all class-level listeners receive notification
2. `StartupInstructionListener` receives `Session` instance
3. Listener **always** renders `_startup.md` for that session
4. If `startup-instruction` flag not set → template filtered by `requires-startup-instruction: true` → returns None
5. If flag is set → template renders with `{{feature_flags.startup-instruction}}` in context
6. If rendered content is non-blank, call `queue_instruction(content, priority=True)` to insert at front of queue
7. Instruction is **fire-and-forget**: queued for next dispatch, no agent acknowledgment expected
8. Agent receives instruction and follows template directives

**No conditional logic needed** - the `requires-*` directive handles filtering automatically.

## Impact
- **Affected specs**: feature-flags, session-management, template-system
- **Affected code**:
  - `src/mcp_guide/session_listener.py` - **BREAKING**: Change protocol signature
  - `src/mcp_guide/session.py` - Make listeners class-level, update notification methods
  - `src/mcp_guide/render/cache.py` - Update `TemplateContextCache` to new signature
  - `src/mcp_guide/workflow/flags.py` - Add flag validation
  - `src/mcp_guide/startup.py` - Create `StartupInstructionListener` class, remove callback code
  - `src/mcp_guide/server.py` - Register listener at startup, remove callback injection
  - `src/mcp_guide/task_manager/manager.py` - Add `priority` parameter to `queue_instruction()`
  - Template: `_startup.md` (already exists)
- **Benefits**:
  - Uses existing template system
  - Consistent with other instruction templates
  - Flexible content targeting via flag
  - Validates configuration at set time
  - Cleaner architecture using class-level listener pattern
  - Single registration point for all sessions
