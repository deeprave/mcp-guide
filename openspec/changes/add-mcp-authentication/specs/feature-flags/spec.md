## ADDED Requirements

### Requirement: Feature-flag mutation authorisation
When provider-backed policy is active for a remote caller, project feature-flag
mutation SHALL require `user` and global feature-flag mutation SHALL require
`admin`. Reading or listing flags SHALL retain existing access
behaviour unless a separate requirement classifies it as protected. When no
provider is selected, remote callers SHALL retain existing behaviour. Stdio
callers SHALL retain unrestricted feature-flag access.

#### Scenario: Caller mutates a global feature flag
- **WHEN** an admin-scoped caller sets or removes a global feature flag
- **THEN** the system SHALL apply the existing validation and persistence rules
- **AND** it SHALL persist the requested mutation

#### Scenario: Caller cannot mutate a global feature flag
- **WHEN** a caller lacks the required scope for global feature-flag mutation
- **THEN** the system SHALL return the corresponding authentication or
  authorisation result
- **AND** it SHALL not change global feature-flag configuration

#### Scenario: Caller mutates a project feature flag
- **WHEN** a user-scoped caller sets or removes a bound project's feature flag
- **THEN** the system SHALL apply the existing project-flag validation and
  persistence rules
