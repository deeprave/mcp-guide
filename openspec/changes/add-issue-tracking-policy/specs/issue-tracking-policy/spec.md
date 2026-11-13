# Spec Delta

## Purpose

Defines an optional policy for linking tracked project work to the commits that deliver it.

## ADDED Requirements

### Requirement: Optional issue-tracking requirement selection
When onboarding a project with a recognised issue tracker, the system SHALL offer a policy that requires issue tracking for commits.

#### Scenario: User enables the policy during onboarding
- **WHEN** the user selects an issue tracker and enables required issue tracking during onboarding
- **THEN** the system configures the policy using the existing policy-selection mechanisms

#### Scenario: User does not enable the policy
- **WHEN** the user selects an issue tracker but declines required issue tracking during onboarding
- **THEN** the system retains the tracker policy that permits proceeding without an issue

### Requirement: Required issue reference before commit
When the required issue-tracking policy is active, the system SHALL require an applicable issue identifier before committing a change unless the user explicitly states that no issue is needed.

#### Scenario: Commit has an applicable issue
- **WHEN** the agent prepares to commit work under the active policy and an issue identifier is available
- **THEN** it associates that issue with the active change or commit before proceeding

#### Scenario: User explicitly waives issue tracking
- **WHEN** the agent prepares to commit work under the active policy and the user explicitly states that no issue is needed
- **THEN** the agent may proceed without an issue identifier

### Requirement: Create and allocate a missing issue
When the required issue-tracking policy is active and no applicable issue exists, the system SHALL instruct the agent to create a corresponding issue through an available tracker integration and allocate it to the active change or commit before committing.

#### Scenario: Tracker integration is available
- **WHEN** the agent needs an issue for a commit and an integration for the selected tracker is available
- **THEN** it creates and allocates an issue before committing

#### Scenario: Tracker integration is unavailable
- **WHEN** the agent needs an issue for a commit and no integration is available
- **THEN** it asks the user how to provide or create the required issue
