## MODIFIED Requirements

### Requirement: Workflow Phase Configuration

The workflow configuration SHALL support `exploration` as an available phase without making it part of the standard ordered workflow sequence.

#### Scenario: Exploration is available but non-ordered
- **WHEN** workflow phases are configured
- **THEN** `exploration` is included in the available/default phase set
- **AND** it is not inserted into the standard ordered sequence of delivery phases

#### Scenario: Leaving exploration requires consent
- **WHEN** the current workflow phase is `exploration`
- **THEN** transitioning out of that phase requires explicit user consent
