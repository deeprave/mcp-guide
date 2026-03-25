## 1. Guide URI instruction template
- [x] 1.1 Create `_system/guide-uri.mustache` template (type: `agent/information`) explaining guide:// URI scheme and read_resource tool
- [x] 1.2 Reference MCP `resources/list` as discovery mechanism, explain read_resource as resolution tool

## 2. GuideUriListener
- [x] 2.1 Create `guide_uri_listener.py` implementing session listener protocol
- [x] 2.2 Render `_system/guide-uri` template on `on_project_changed`
- [x] 2.3 Queue rendered content via `task_manager.queue_instruction()` (no ack, no priority)
- [x] 2.4 Register listener in session listener setup
- [x] 2.5 Add tests for listener rendering and queueing

## 3. Content accessor lambda
- [x] 3.1 Add `resource` lambda to `render/functions.py` following existing lambda patterns
- [x] 3.2 Default rendering: `guide://expression` URI format
- [x] 3.3 When `content-accessor` flag is `true`: render as `get_content("expression")`
- [x] 3.4 Register `content-accessor` feature flag with validator
- [x] 3.5 Add tests for lambda rendering in both modes

## 4. Template migration
- [x] 4.1 Replace `{{tool_prefix}}get_content("...")` references in templates with `{{#resource}}...{{/resource}}`
- [x] 4.2 Verify all templates render correctly with default flag value
- [x] 4.3 Verify templates render correctly with `content-accessor: true`

## 5. Check
- [x] 5.1 Run full test suite, lint, type checks, format
