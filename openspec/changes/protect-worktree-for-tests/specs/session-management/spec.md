## ADDED Requirements

### Requirement: Session Does Not Own Process Docroot Or Global Flags
A Session SHALL NOT own process document-root or global feature-flag state.
Callers that need those values SHALL obtain them from the process runtime.
A Session MAY keep project-scoped flag access for the bound project.

#### Scenario: Docroot is requested
- **WHEN** application code needs the process document root
- **THEN** it SHALL obtain it from the process runtime
- **AND** it SHALL NOT treat Session as the owner of that path

#### Scenario: Global flags are requested
- **WHEN** application code needs global feature flags
- **THEN** it SHALL obtain them from the process runtime
- **AND** Session SHALL NOT expose a global-flag ownership API

#### Scenario: Project flags remain interaction-scoped
- **WHEN** application code needs flags stored on the bound project
- **THEN** it SHALL continue to use the Session's bound project configuration

#### Scenario: Session configuration accessor
- **WHEN** Session code needs the process configuration service for project
  operations
- **THEN** it SHALL obtain that service from its process runtime
- **AND** it SHALL NOT import the configuration-service class
