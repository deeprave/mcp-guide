# Change: Add guide:// URI instruction and content accessor lambda

**Status**: Proposed
**Priority**: High
**Complexity**: Medium

## Why

- Agents have no automatic way to learn about the `guide://` URI scheme. MCP `resources/list` is ignored by most agents. The `read_resource` tool description alone is insufficient — agents don't proactively connect `guide://` URIs encountered in content with a tool called `read_resource`.
- Templates currently hardcode `get_content("expression")` references via `{{tool_prefix}}get_content`. With `read_resource` now available, templates should be able to render content references as `guide://` URIs instead, giving agents a choice of access method. This needs to be switchable via feature flag.
- Complex expressions (comma-separated collections/categories) are not valid as guide:// URIs since commas are not valid in the URI authority field. The lambda must fall back to `get_content()` for these.

## What Changes

### 1. One-shot guide:// URI instruction

- Add template `_system/guide-uri.mustache` (type: `agent/information`) that explains:
  - The `guide://` URI scheme exists and is listed in MCP `resources/list`
  - Content URIs: `guide://expression[/pattern]`
  - Command URIs: `guide://_command[/args][?kwargs]`
  - URIs can be resolved via the `read_resource` tool
- Add `GuideUriListener` session listener that:
  - Fires on `on_project_changed`
  - Renders the template via `render_content`
  - Queues via `task_manager.queue_instruction()` (no ack, no priority)
  - One-shot, not user-visible, not gated by feature flag
- Register listener in session listener setup alongside `StartupInstructionListener`

### 2. Content accessor template lambda

- Add `{{#resource}}expression{{/resource}}` template lambda that renders content references
- Controlled by `content-accessor` feature flag:
  - `false` (default): renders as `guide://expression` URI
  - `true`: renders as `get_content("expression")`
- For MVP, complex expressions containing commas always fall back to `get_content("expression")` regardless of flag, since guide:// URIs don't support comma-separated values in the authority field
- Replace existing `{{tool_prefix}}get_content("...")` references in templates with `{{#resource}}...{{/resource}}`

## Technical Approach

### GuideUriListener

Follows the same pattern as `StartupInstructionListener`:
- Implements session listener protocol (`on_config_changed`, `on_project_changed`)
- Renders `_system/guide-uri.mustache` via `render_content(pattern="guide-uri", category_dir="_system")`
- Queues result via `task_manager.queue_instruction(content)` — no priority, no ack
- Fires after startup instruction (natural ordering from listener registration)

### Resource lambda

- Implemented as a class-based lambda in `render/functions.py` following existing lambda patterns
- Receives the expression text, checks for commas → if present, always renders `get_content("expr")`
- Otherwise checks `content-accessor` flag value to determine rendering format
- Registered in template context as `resource`

## Success Criteria

- Agent receives guide:// URI instruction on first tool call without user action
- Templates render content references as `guide://` URIs by default
- Setting `content-accessor: true` switches to `get_content()` rendering
- Complex expressions with commas always render as `get_content()`
