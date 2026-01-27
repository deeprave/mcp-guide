# task-manager Specification Delta

## MODIFIED Requirements

### Requirement: Event Dispatch Return Format
The system SHALL return structured data from event dispatch with all handler results.

#### Scenario: Multiple handlers process event
- WHEN multiple subscribers handle the same event
- THEN dispatch_event SHALL return dict containing:
  - `processed_count`: Number of handlers that processed the event
  - `handlers`: List of handler results with optional template info
- AND each handler result MAY include:
  - `template`: Template name to render
  - `template_type`: Type of template (openspec, workflow, common)
  - `context`: Additional context data for template

#### Scenario: No handlers process event
- WHEN no subscribers handle an event
- THEN dispatch_event SHALL return `{processed_count: 0, handlers: []}`
- AND no template rendering occurs

#### Scenario: Handler without template
- WHEN a handler processes event without template info
- THEN handler result is included in handlers list
- AND no template field is present for that handler

## ADDED Requirements

### Requirement: Dispatcher Function
The system SHALL provide a dispatcher function that handles template rendering above dispatch_event.

#### Scenario: Dispatch with template rendering
- WHEN dispatcher is called with event data
- THEN it SHALL call dispatch_event to collect handler results
- AND for each handler result with template info:
  - Render template using appropriate function based on template_type
  - Pass additional context to template renderer
- AND return Result with rendered content

#### Scenario: Dispatch without templates
- WHEN no handlers return template info
- THEN dispatcher SHALL return Result.ok() without echoing data
- AND no unnecessary data is included in response

#### Scenario: Template type routing
- WHEN template_type is "openspec"
- THEN use OpenSpec template rendering function
- WHEN template_type is "workflow"
- THEN use workflow template rendering function
- WHEN template_type is "common"
- THEN use common template rendering function

## REMOVED Requirements

### Requirement: Event Handler Result Return
Event handlers SHALL NOT return Result objects directly.

#### Scenario: Handler returns dict format
- WHEN event handler processes event
- THEN it SHALL return dict with optional template info
- AND NOT return Result object
