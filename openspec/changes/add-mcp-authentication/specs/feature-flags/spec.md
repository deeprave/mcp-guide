## ADDED Requirements

### Requirement: Feature-flag mutation authorisation
For HTTP(S) callers, global feature-flag mutation SHALL require the `admin`
scope and project feature-flag mutation SHALL require the `user` scope. Reading
or listing flags SHALL retain its existing access behaviour unless a separate
requirement classifies it as protected. Stdio callers SHALL retain unrestricted
feature-flag access.

#### Scenario: Admin mutates a global feature flag
- **WHEN** an `admin`-scoped caller sets or removes a global feature flag
- **THEN** the system SHALL apply the existing validation and persistence rules
- **AND** it SHALL persist the requested mutation

#### Scenario: Caller without admin scope mutates a global feature flag
- **WHEN** an unauthenticated or non-admin caller sets or removes a global
  feature flag
- **THEN** the system SHALL return an authorisation failure
- **AND** it SHALL not change the global feature-flag configuration

#### Scenario: User mutates a project feature flag
- **WHEN** a `user`-scoped caller sets or removes a feature flag for its bound
  project
- **THEN** the system SHALL apply the existing project-flag validation and
  persistence rules
