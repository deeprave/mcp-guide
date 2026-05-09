## ADDED Requirements

### Requirement: Safe Documentation Update Targets
The system SHALL treat documentation updates as valid only when the resolved
documentation root is safe for update operations.

The same docroot safety rule SHALL be used both when determining whether an
update may be attempted and when executing the installer-side update path.

#### Scenario: Template source docroot is rejected
- **WHEN** the resolved documentation root is the template source directory
- **THEN** the system SHALL treat that docroot as non-updateable
- **AND** the installer-side update path SHALL reject update execution for that docroot

#### Scenario: Valid installed docroot remains updateable
- **WHEN** the resolved documentation root is not the template source directory
- **THEN** the system SHALL allow normal update eligibility checks to continue
- **AND** docroot safety validation SHALL not by itself suppress the update

