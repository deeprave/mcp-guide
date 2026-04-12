## MODIFIED Requirements

### Requirement: Onboarding Covers Workflow Preferences

The onboarding system SHALL support user choice over workflow behavior using a
defined set of onboarding-facing workflow modes that map to valid `workflow`
project flag values.

#### Scenario: User disables workflow during onboarding
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `none` or `unstructured`
- **THEN** onboarding maps that choice to `workflow: false`

#### Scenario: User selects structured workflow shorthand
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `structured`
- **THEN** onboarding maps that choice to `workflow: true`

#### Scenario: User selects simple workflow
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `simple`
- **THEN** onboarding maps that choice to `workflow: [discussion, implementation, exploration]`

#### Scenario: User selects developer workflow
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `developer`
- **THEN** onboarding maps that choice to `workflow: [discussion, implementation, review, exploration]`

#### Scenario: User selects full workflow
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `full`
- **THEN** onboarding maps that choice to `workflow: [discussion, planning, implementation, check, review, exploration]`

#### Scenario: Full workflow is the explicit full-sequence option
- **WHEN** onboarding presents workflow-related setup choices
- **THEN** `structured` is available as the boolean shorthand for the standard
  enabled workflow
- **AND** `full` is available as the explicit onboarding option for the full
  ordered phase sequence
- **AND** both options map to server-valid workflow configurations

## ADDED Requirements

### Requirement: Exploration Remains Non-Linear In Workflow Variants

Workflow variants exposed during onboarding SHALL treat `exploration` as an
available exploratory mode rather than a normal ordered delivery phase.

#### Scenario: Exploration is available in all workflow-enabled variants
- **WHEN** onboarding presents any workflow-enabled choice
- **THEN** the resulting workflow configuration includes `exploration` as an
  available phase

#### Scenario: Exploration is not available when workflow is disabled
- **WHEN** onboarding maps the selected workflow choice to `workflow: false`
- **THEN** workflow tracking is disabled
- **AND** `exploration` is not presented as available through the workflow
  system

#### Scenario: Exploration is not treated as an ordered predecessor or successor
- **WHEN** onboarding describes or applies workflow variants that include
  `exploration`
- **THEN** it does not describe `exploration` as having a natural previous or
  next delivery phase
- **AND** it treats `exploration` as a mode for investigating approaches,
  testing alternatives, and often drafting OpenSpec proposals

#### Scenario: Exploration remains distinct from discussion
- **WHEN** onboarding explains workflow variants containing `exploration`
- **THEN** it distinguishes `exploration` from `discussion`
- **AND** it describes `discussion` as alignment-oriented
- **AND** it describes `exploration` as approach-oriented
