## ADDED Requirements

### Requirement: Content Accessor Lambda

The system SHALL provide a `resource` template lambda that renders content references in a configurable format.

The resource lambda SHALL:
- Accept an expression string and render it as a content reference
- Default to `guide://expression` URI format when `content-accessor` flag is `false` or unset
- Render as `get_content("expression")` when `content-accessor` flag is `true`
- Be registered in the template context as `resource`

#### Scenario: Default rendering (guide:// URI)
- WHEN `{{#resource}}guidelines{{/resource}}` is rendered
- AND `content-accessor` flag is `false` or unset
- THEN output is `guide://guidelines`

#### Scenario: Tool rendering
- WHEN `{{#resource}}guidelines{{/resource}}` is rendered
- AND `content-accessor` flag is `true`
- THEN output is `get_content("guidelines")`

### Requirement: Guide URI Instruction Delivery

The system SHALL automatically inform agents about the guide:// URI scheme via a one-shot instruction.

Guide URI instruction delivery SHALL:
- Render `_system/guide-uri.mustache` template on project load
- Queue the rendered content as a non-priority instruction (no acknowledgement)
- Reference MCP `resources/list` as the standard discovery mechanism
- Explain that `read_resource` tool resolves guide:// URIs
- Not require a feature flag (always active)
- Not be user-visible
- Use `agent/information` template type

#### Scenario: Instruction delivery on project load
- WHEN a project is loaded for the first time in a session
- THEN the guide URI instruction is queued for delivery on next tool response

#### Scenario: Instruction is one-shot
- WHEN the guide URI instruction has been queued
- THEN it is not retried or re-queued on subsequent tool calls
