# onboarding-state Specification

## Purpose
Tracks guided onboarding state and provides onboarding notifications for projects.

## Requirements

### Requirement: Onboarding State Tracking

The system SHALL track whether guided onboarding has been completed for a project using a project-level flag.

#### Scenario: Onboarding flag is unset for a new project
- **WHEN** a project is first created or has not yet been onboarded
- **THEN** the `onboarded` project flag is absent or `false`

#### Scenario: Onboarding flag is set on completion
- **WHEN** the user confirms the final onboarding step
- **AND** the system applies the resulting configuration changes
- **THEN** the `onboarded` project flag is set to `true` as part of that same atomic update

#### Scenario: Onboarding command is available regardless of flag state
- **WHEN** a user invokes the `:onboard` command or `guide://_onboard` URI
- **THEN** the onboarding flow runs regardless of whether `onboarded` is `true` or `false`
- **AND** completing the flow sets `onboarded` to `true`

#### Scenario: User skips onboarding to suppress future notifications
- **WHEN** a user invokes `:onboard --skip` or `guide://_onboard?skip`
- **THEN** the onboarding flow does not run
- **AND** the `onboarded` flag is set to `true`, suppressing future startup notifications
- **AND** the user is informed that they can run `:onboard` at any time to configure their project

### Requirement: Onboarding Notification on Project Load

When a project is loaded and onboarding has not been completed, the system SHALL notify the user that guided onboarding is available.

#### Scenario: Notification shown when onboarding not completed
- **WHEN** a project is loaded or the session is established
- **AND** the `onboarded` project flag is absent or `false`
- **THEN** the system surfaces a `user/information` notification explaining that onboarding is available and how to invoke it
- **AND** the notification is presented to the user, not acted on by the agent

#### Scenario: Notification repeats until onboarding is complete
- **WHEN** the project is loaded in subsequent sessions
- **AND** `onboarded` is still `false` or absent
- **THEN** the notification is shown again

#### Scenario: Notification is suppressed after onboarding
- **WHEN** the `onboarded` project flag is `true`
- **THEN** no onboarding notification is shown on project load

### Requirement: Atomic Configuration Application

The onboarding flow SHALL stage all configuration changes in the agent's working context and apply them as a single confirmed update.

#### Scenario: Changes are staged before application
- **WHEN** the user works through onboarding choices
- **THEN** the resulting configuration changes are held in the agent's working context
- **AND** not applied piecemeal to the project configuration

#### Scenario: User confirms before changes are applied
- **WHEN** onboarding reaches the final step
- **THEN** the agent presents a summary of all pending configuration changes
- **AND** waits for user confirmation before applying any of them

#### Scenario: Configuration applied atomically on confirmation
- **WHEN** the user confirms the onboarding summary
- **THEN** all configuration changes are applied through existing mechanisms (profiles, flags, policy selections, etc.)
- **AND** the `onboarded` flag is set to `true` as part of the same update
