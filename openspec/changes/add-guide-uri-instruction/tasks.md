## 1. Guide URI instruction template
- [ ] 1.1 Create `_system/guide-uri.mustache` template (type: `agent/information`) explaining guide:// URI scheme and read_resource tool
- [ ] 1.2 Reference MCP `resources/list` as discovery mechanism, explain read_resource as resolution tool

## 2. GuideUriListener
- [ ] 2.1 Create `guide_uri_listener.py` implementing session listener protocol
- [ ] 2.2 Render `_system/guide-uri` template on `on_project_changed`
- [ ] 2.3 Queue rendered content via `task_manager.queue_instruction()` (no ack, no priority)
- [ ] 2.4 Register listener in session listener setup
- [ ] 2.5 Add tests for listener rendering and queueing

## 3. Content accessor lambda
- [ ] 3.1 Add `resource` lambda to `render/functions.py` following existing lambda patterns
- [ ] 3.2 Default rendering: `guide://expression` URI format
- [ ] 3.3 When `content-accessor` flag is `true`: render as `get_content("expression")`
- [ ] 3.4 Complex expressions (containing commas): always fall back to `get_content("expression")`
- [ ] 3.5 Register `content-accessor` feature flag with validator
- [ ] 3.6 Add tests for lambda rendering in both modes and comma fallback

## 4. Template migration
- [ ] 4.1 Replace `{{tool_prefix}}get_content("...")` references in templates with `{{#resource}}...{{/resource}}`
- [ ] 4.2 Verify all templates render correctly with default flag value
- [ ] 4.3 Verify templates render correctly with `content-accessor: true`

## 5. Check
- [ ] 5.1 Run full test suite, lint, type checks, format
