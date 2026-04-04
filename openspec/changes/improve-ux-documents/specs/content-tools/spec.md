## ADDED Requirements

### Requirement: Document Update Command Remains Inline by Default

The `:document/update` command SHALL remain an inline mutation command unless a concrete handoff-oriented benefit is established during implementation.

#### Scenario: Update remains inline
- **WHEN** `:document/update` is rendered
- **THEN** the template continues to instruct the agent to call the update tool inline
- **AND** it does not require a handoff branch merely for consistency with ingestion or export commands
