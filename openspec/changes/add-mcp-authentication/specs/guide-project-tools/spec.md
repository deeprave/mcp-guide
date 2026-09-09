## ADDED Requirements

### Requirement: Project-administration authorisation
For HTTP(S) callers, project binding, project selection, project cloning, and
persisted project configuration mutation SHALL require the `user` scope.
Project reads and unprotected discovery operations SHALL retain their existing
access behaviour. Stdio callers SHALL retain unrestricted project
administration.

#### Scenario: User binds or selects a project
- **WHEN** a `user`-scoped caller invokes `set_project` or `switch_project`
- **THEN** the system SHALL apply the existing root-validation and session
  lifecycle requirements
- **AND** it SHALL permit the requested binding or selection

#### Scenario: Unauthenticated caller attempts project administration
- **WHEN** an unauthenticated caller invokes a project-administration operation
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL not create, select, clone, or mutate a project configuration

#### Scenario: Admin administers a project
- **WHEN** an `admin`-scoped caller invokes a project-administration operation
- **THEN** the system SHALL treat the caller as authorised with the `user`
  scope
