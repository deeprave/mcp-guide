## MODIFIED Requirements

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

#### Scenario: User skips a single dimension
- **WHEN** the user responds with `skip` or an empty answer for the current onboarding dimension
- **THEN** onboarding leaves that dimension unchanged
- **AND** continues to the next remaining dimension

#### Scenario: User skips all remaining dimensions
- **WHEN** the user responds with `skip-all` during onboarding
- **THEN** onboarding stops asking the remaining unanswered dimensions
- **AND** preserves any answers already staged in the current onboarding run
- **AND** proceeds to the final confirmation summary for the staged changes
