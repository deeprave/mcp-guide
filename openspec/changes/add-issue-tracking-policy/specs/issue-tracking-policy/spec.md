# Spec Delta

## Purpose

Defines the policy for linking tracked project work to the commits that deliver it.

## ADDED Requirements

### Requirement: Selected issue tracker enables required issue tracking
When a project selects a recognised issue tracker, the system SHALL require issue tracking for eligible changes without an additional project flag or onboarding choice.

#### Scenario: User selects a recognised tracker
- **WHEN** the user selects a recognised issue tracker during onboarding
- **THEN** the system configures required issue tracking through the selected provider policy

#### Scenario: User selects no tracker
- **WHEN** the user selects `None` during onboarding
- **THEN** the system does not require issue tracking

### Requirement: Required issue reference before commit
When a recognised issue-tracking provider is selected and the active change is tracked, the system SHALL require an applicable issue identifier before committing.

#### Scenario: Small bug fix defaults to untracked
- **WHEN** the active change is a small bug fix
- **THEN** the system treats it as untracked by default

#### Scenario: Change not tracked in OpenSpec defaults to untracked
- **WHEN** OpenSpec is active and the active change is not tracked in OpenSpec
- **THEN** the system treats it as untracked by default

#### Scenario: OpenSpec-tracked non-bug-fix change defaults to tracked
- **WHEN** OpenSpec is active and the active change is tracked in OpenSpec and is more than a bug fix
- **THEN** the system treats it as tracked by default

#### Scenario: Tracking status is unclear
- **WHEN** the agent cannot determine whether the active change requires tracking
- **THEN** it asks the user before creating or linking an issue

#### Scenario: Commit has an applicable issue
- **WHEN** the agent prepares to commit work under the active policy and an issue identifier is available
- **THEN** it associates that issue with the active change or commit before proceeding

#### Scenario: User explicitly waives issue tracking
- **WHEN** the agent prepares to commit work under the active policy and the user explicitly states that no issue is needed
- **THEN** the agent may proceed without an issue identifier

### Requirement: Create and allocate a missing issue
When a recognised issue-tracking provider is selected, the active change is tracked, and no applicable issue exists, the system SHALL instruct the agent to create a corresponding issue through an available tracker integration and allocate it to the active change or commit before committing.

#### Scenario: Tracker integration is available
- **WHEN** the agent needs an issue for a commit and an integration for the selected tracker is available
- **THEN** it creates and allocates an issue before committing

#### Scenario: Tracker integration is unavailable
- **WHEN** the agent needs an issue for a commit and no integration is available
- **THEN** it asks the user how to provide or create the required issue
