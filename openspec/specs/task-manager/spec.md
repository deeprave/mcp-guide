# task-manager Specification

## Purpose
TBD - created by archiving change refactor-dispatch-handler. Update Purpose after archive.
## Requirements
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

