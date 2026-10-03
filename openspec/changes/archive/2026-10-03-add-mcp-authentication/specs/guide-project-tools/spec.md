## ADDED Requirements

### Requirement: Unprotected project binding and selection
`set_project` and `switch_project` SHALL retain their existing access behaviour
when provider-backed policy is active. They SHALL remain available so a caller
can establish or select a usable project without authenticating, including when
the first binding creates that project's configuration.

#### Scenario: Unauthenticated caller binds a project
- **WHEN** a caller invokes `set_project` while the provider is active
- **THEN** the system SHALL apply existing root-validation and session-lifecycle
  requirements
- **AND** it SHALL permit the binding without an authorisation decision

#### Scenario: Unauthenticated caller switches project
- **WHEN** a caller invokes `switch_project` while the provider is active
- **THEN** the system SHALL preserve existing project-selection behaviour

### Requirement: Project configuration authorisation
When provider-backed policy is active, profiles, project flags, categories,
collections, and other persisted project-configuration mutations SHALL require
`user`. Project onboarding SHALL permit unauthenticated inspection of existing
configuration and collection or confirmation of choices. It SHALL require `user`
access before persisting any settings, including marking onboarding as skipped.
Cloning SHALL require `admin`.

#### Scenario: Caller applies onboarding configuration
- **WHEN** a user-scoped caller confirms onboarding settings
- **THEN** the system SHALL apply the existing configuration behaviour

#### Scenario: Caller cannot apply onboarding configuration
- **WHEN** authentication is active and the caller lacks `user`
- **THEN** onboarding SHALL explain that authentication is required before saving
- **AND** the system SHALL not persist onboarding configuration or mark it skipped

#### Scenario: Unauthenticated caller reviews onboarding preferences
- **WHEN** authentication is active and the caller lacks `user`
- **THEN** onboarding SHALL permit inspection of existing configuration and
  collection of choices without persisting them

#### Scenario: Administrator clones a project
- **WHEN** an admin-scoped caller invokes `clone_project`
- **THEN** the system SHALL apply the existing atomic clone behaviour

#### Scenario: Non-administrator cannot clone a project
- **WHEN** a caller without `admin` invokes `clone_project`
- **THEN** the system SHALL return an insufficient-authorisation result
- **AND** it SHALL not create or alter the clone

### Requirement: Project permission authorisation
When provider-backed policy is active, project permission-path mutation SHALL
require `admin`.

#### Scenario: Caller changes project permission paths
- **WHEN** an admin-scoped caller changes project permission paths
- **THEN** the system SHALL apply the existing permission-path validation and
  persistence behaviour
