## ADDED Requirements

### Requirement: Onboarding Covers Workflow Preferences

The onboarding system SHALL support user choice over workflow behavior.

#### Scenario: User selects workflow mode during onboarding
- **WHEN** onboarding presents workflow-related setup choices
- **THEN** the user can choose whether workflow handling is enabled
- **AND** the user can choose between simpler and more structured workflow approaches where supported
- **AND** the resulting workflow configuration is applied through the existing workflow flag model
