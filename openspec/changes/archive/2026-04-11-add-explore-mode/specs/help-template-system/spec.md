## MODIFIED Requirements

### Requirement: Workflow Phase Templates

The workflow template set SHALL include a dedicated exploration phase template.

#### Scenario: Exploration phase template exists
- **WHEN** workflow phase templates are rendered
- **THEN** `_workflow/06-exploration.mustache` exists
- **AND** it provides concise guidance for investigation, requirement discovery, and option exploration
- **AND** it explicitly forbids implementation while in that phase

#### Scenario: Explore command template exists
- **WHEN** workflow command templates are rendered
- **THEN** `_commands/workflow/explore.mustache` exists
- **AND** it mirrors the issue-handling pattern used by `:workflow/discuss`
