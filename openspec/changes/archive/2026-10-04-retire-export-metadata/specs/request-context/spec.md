# Spec Delta

## MODIFIED Requirements

### Requirement: Bound Root and Active Project Access

A bound RequestContext SHALL expose its Session's immutable root identity and
current Project configuration, including categories, collections, flags,
permissions and configuration identity. Unbound contexts SHALL expose
absent root and project values.

Project configuration values may change through the owning Session, but a
bound Session's project/root identity SHALL NOT be redirected by a switch.
Replacing runtime's current instance SHALL NOT make an existing context read
the replacement's state.

#### Scenario: Bound request reads active project data
- **WHEN** an admitted request reads bound project data
- **THEN** its context SHALL expose its captured Session's root path, name and hash
- **AND** project access SHALL use that Session without another ID lookup

#### Scenario: Project configuration changes during a request
- **WHEN** an operation updates its Session's project configuration
- **THEN** it SHALL perform the update through that Session
- **AND** subsequent project access through its context SHALL see that Session's current configuration
- **AND** the context SHALL NOT keep a separate stale Project snapshot

#### Scenario: Bound root tracks in-request bind
- **GIVEN** the context holds an initially unbound Session
- **WHEN** that instance successfully receives its first binding
- **THEN** the existing context SHALL expose the root and become bound
- **AND** rebuilding the context SHALL NOT be necessary

#### Scenario: Old context remains attached to the original project
- **GIVEN** an admitted request's Session has become expiring
- **WHEN** that request reads or updates project configuration
- **THEN** it SHALL still use its original project's identity
- **AND** a replacement under the same public ID SHALL NOT redirect its access
