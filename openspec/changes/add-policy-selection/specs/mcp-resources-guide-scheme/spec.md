## ADDED Requirements

### Requirement: Selected Policy Topic Resolution

The guide resource scheme SHALL support resolution of policy topics according to the active project policy selection.

#### Scenario: Policy topic resolves selected guidance
- **WHEN** a guide resource requests a policy topic such as `guide://policy/scm`
- **THEN** the system resolves the selected applicable policy guidance for that topic
- **AND** it does not return every available policy alternative by default

#### Scenario: Policy topic follows project selection
- **WHEN** a project's active policy selection changes
- **THEN** subsequent `guide://policy/<topic>` resolution reflects the updated selection for that project
