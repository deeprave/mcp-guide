## ADDED Requirements

### Requirement: Conditional workflow command detail
Workflow command templates SHALL conditionally render workflow-specific details without using workflow requirements to suppress their general content.

#### Scenario: Workflow requirement is absent
- **WHEN** a workflow command template is discovered while workflow is disabled
- **THEN** its general command content SHALL remain discoverable and renderable
