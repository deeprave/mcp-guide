# task-manager Specification Delta

## ADDED Requirements

### Requirement: EventResult Composite Object
The system SHALL define an EventResult dataclass to represent handler results.

#### Scenario: EventResult structure
- GIVEN an event handler processes an event
- THEN it SHALL return EventResult with:
  - `result: bool` - True for success, False for failure
  - `message: Optional[str]` - Simple string result or error message
  - `rendered_content: Optional[RenderedContent]` - Rendered template content if applicable

#### Scenario: Simple result without rendering
- WHEN handler completes without template rendering
- THEN EventResult SHALL have:
  - `result: True` or `False`
  - `message: str` with result description
  - `rendered_content: None`

#### Scenario: Result with rendered content
- WHEN handler renders a template
- THEN EventResult SHALL have:
  - `result: True`
  - `message: Optional[str]` (may be None)
  - `rendered_content: RenderedContent` with content and instruction

## ADDED Requirements

### Requirement: Event Dispatch Return Format
The system SHALL return list of EventResult objects from event dispatch.

#### Scenario: Multiple handlers process event
- WHEN multiple subscribers handle the same event
- THEN dispatch_event SHALL return `list[EventResult]`
- AND list contains results from all handlers that processed the event

#### Scenario: No handlers process event
- WHEN no subscribers handle an event
- THEN dispatch_event SHALL return empty list `[]`
- AND aggregate_event_results SHALL return Result.ok(instruction="") with no message or value

#### Scenario: Single handler processes event
- WHEN one subscriber handles an event
- THEN dispatch_event SHALL return list with one EventResult

## ADDED Requirements

### Requirement: Result Construction from EventResult
The system SHALL construct Result objects from EventResult list with aggregation.

#### Scenario: Single EventResult with rendered content
- WHEN EventResult contains rendered_content
- THEN Result SHALL use:
  - `success: True`
  - `value: rendered_content.content`
  - `instruction: rendered_content.instruction` (RenderedContent handles resolution)
  - `message: EventResult.message` if present

#### Scenario: Single EventResult without rendered content
- WHEN EventResult has no rendered_content
- THEN Result SHALL have:
  - `success: EventResult.result`
  - `message: EventResult.message`
  - `instruction: <default for success/failure>`
  - `value: None`

#### Scenario: Multiple EventResults aggregation
- WHEN dispatch returns multiple EventResults
- THEN Result SHALL aggregate:
  - Success if all EventResult.result are True
  - Messages: Deduplicate and concatenate all EventResult.message values
  - Content: Concatenate all rendered_content.content values in order (if any)
  - Instruction: Use existing deduplication logic from render package for all rendered_content.instruction values

#### Scenario: Mixed rendered and non-rendered results
- WHEN some EventResults have rendered_content and others don't
- THEN Result SHALL:
  - Combine all messages (from both rendered and non-rendered)
  - Combine all rendered content in order
  - Use instruction deduplication on rendered_content.instruction values

## REMOVED Requirements

### Requirement: Template Type Routing
Handlers SHALL NOT use template type routing (openspec, workflow, common).

#### Scenario: Handler renders template
- WHEN handler needs to render template
- THEN it SHALL call appropriate render function directly
- AND return EventResult with rendered_content
- AND NOT specify template_type for routing

### Requirement: Dispatcher Function
The system SHALL NOT have a separate dispatcher function above dispatch_event.

#### Scenario: Template rendering responsibility
- WHEN handler needs template rendering
- THEN handler SHALL render template itself
- AND return EventResult with rendered_content
- AND dispatch_event simply collects EventResult objects
