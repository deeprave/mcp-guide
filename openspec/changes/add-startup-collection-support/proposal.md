# Change: Add Startup Instruction Support

## Why
When a project loads or switches, agents need immediate access to critical startup instructions. Currently, there's no mechanism to automatically inject project-specific instructions that guide the agent's initial context and behaviour.

## What Changes

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

### Add `_startup.mustache` Template
- **Location**: Project docroot
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
Render and queue `_startup.mustache` when:
1. **Project loads** (server startup with existing project)
2. **Project switches** (user changes to different project)

### Rendering Flow
1. On project load/switch, **always** render `_startup.mustache`
2. If `startup-instruction` flag not set → template filtered by `requires-startup-instruction: true` → returns None
3. If flag is set → template renders with `{{feature_flags.startup-instruction}}` in context
4. If rendered content is non-blank, call `queue_instruction(content, priority=True)` to insert at front of queue
5. Instruction is **fire-and-forget**: queued for next dispatch, no agent acknowledgment expected
6. Agent receives instruction and follows template directives

**No conditional logic needed** - the `requires-*` directive handles filtering automatically.

## Impact
- **Affected specs**: feature-flags, session-management, template-system
- **Affected code**:
  - `src/mcp_guide/workflow/flags.py` - Add flag validation
  - `src/mcp_guide/guide.py` - Project load/switch detection
  - `src/mcp_guide/task_manager/manager.py` - Add `priority` parameter to `queue_instruction()`
  - Template: `_startup.mustache` (new)
- **Benefits**:
  - Uses existing template system
  - Consistent with other instruction templates
  - Flexible content targeting via flag
  - Validates configuration at set time
