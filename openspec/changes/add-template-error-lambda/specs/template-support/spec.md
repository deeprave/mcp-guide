## ADDED Requirements

### Requirement: Template Error Signaling
The system SHALL provide an `_error` template lambda that allows templates to signal application-level errors through the rendering pipeline.

The `_error` lambda SHALL:
- Be registered in the common rendering pipeline, available to all template types (command, openspec, workflow, context)
- Render the enclosed block content using the current template context
- Append the rendered error message to a list on the `TemplateFunctions` instance
- Return an empty string so no error content appears in the rendered output
- Support multiple invocations, accumulating all errors

#### Scenario: Template signals missing argument error
- **WHEN** a command template renders `{{#_error}}Missing required argument{{/_error}}`
- **THEN** the rendered output SHALL NOT contain the error message
- **AND** the error message SHALL be captured by the rendering pipeline

#### Scenario: Multiple errors accumulated
- **WHEN** a template invokes `_error` multiple times
- **THEN** all error messages SHALL be collected in order
- **AND** `RenderedContent.errors` SHALL contain all messages

#### Scenario: Errors propagate through RenderedContent
- **WHEN** a template signals one or more errors via `_error` lambda
- **THEN** `RenderedContent.errors` SHALL contain the error messages
- **AND** callers SHALL handle errors appropriately for their context

#### Scenario: No error signaled
- **WHEN** a template renders without invoking `_error`
- **THEN** `RenderedContent.errors` SHALL be an empty list
- **AND** the result SHALL proceed as normal

#### Scenario: Error with rendered context variables
- **WHEN** a template renders `{{#_error}}Missing: {{variable_name}}{{/_error}}`
- **THEN** the error message SHALL contain the rendered value of `variable_name`

#### Scenario: Available across all template types
- **WHEN** any template type (command, openspec, workflow, context) is rendered through the common pipeline
- **THEN** the `_error` lambda SHALL be available for use
- **AND** errors SHALL propagate via `RenderedContent.errors` to the respective caller

#### Scenario: Errors from partials propagate to parent
- **WHEN** a partial template invokes `{{#_error}}...{{/_error}}`
- **THEN** the error SHALL accumulate in the same `RenderedContent.errors` as the parent template

### Requirement: Template Name Context Variable
The system SHALL inject `template_name` into the template context during rendering.

`template_name` SHALL be the stem of the template file path with any leading underscore stripped.

#### Scenario: template_name available in error messages
- **WHEN** a template renders `{{#_error}}Error in {{template_name}}: missing argument{{/_error}}`
- **THEN** the error message SHALL contain the resolved template name

### Requirement: Command Template Error Handling
When `_execute_command` renders a command template that signals errors via `_error`, it SHALL return a failure result.

The failure result SHALL:
- Set `error` to the newline-joined error messages
- Set `error_type` to `"validation"`
- Set `error_data` to `{"errors": [list of individual error messages]}`

#### Scenario: Command template signals validation error
- **WHEN** a command template invokes `{{#_error}}Missing required argument: name{{/_error}}`
- **THEN** `_execute_command` SHALL return `Result.failure` with `error_type="validation"`
- **AND** `error_data["errors"]` SHALL contain the error message
- **AND** the tool response SHALL have `success: false`
