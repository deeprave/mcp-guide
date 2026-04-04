## MODIFIED Requirements

### Requirement: Workflow Commands

The workflow command set SHALL provide an explicit command for entering exploration mode.

#### Scenario: Explore command retains current issue
- **WHEN** the user invokes `:workflow/explore` with no issue argument
- **THEN** the workflow phase changes to `exploration`
- **AND** the current issue remains unchanged

#### Scenario: Explore command switches issue explicitly
- **WHEN** the user invokes `:workflow/explore <issue>`
- **THEN** the workflow phase changes to `exploration`
- **AND** the current issue is updated to `<issue>`

#### Scenario: Explore alias is available
- **WHEN** workflow commands are discovered
- **THEN** `:explore` is available as an alias for `:workflow/explore`

### Requirement: Exploratory Issue Suggestion

The workflow system SHALL treat exploratory issue names as a suggestion trigger for exploration mode.

#### Scenario: Exploratory issue suggests exploration mode
- **WHEN** the current issue begins with `explor`
- **THEN** the system suggests entering `exploration`
- **AND** it asks the user for consent before switching
- **AND** it does not switch automatically
