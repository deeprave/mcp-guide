## MODIFIED Requirements

### Requirement: Smart Update Strategy
The system SHALL use intelligent update strategy based on file modification
status and upstream document set changes.

#### Scenario: File unchanged from original and differs from new version
- **WHEN** current file matches original in the previous install archive
- **AND** current file differs from new version
- **THEN** file is updated to new version without backup
- **AND** no user changes are lost

#### Scenario: File modified by user
- **WHEN** current file differs from original in the previous install archive
- **THEN** diff is computed against the original version
- **AND** the change is patched or replaced using existing conflict behavior

#### Scenario: Upstream removed file unchanged locally
- **WHEN** a file exists in the previous install archive
- **AND** that file is absent from the new template set
- **AND** the current local file matches the previous original content
- **THEN** the local file is deleted during update

#### Scenario: Upstream removed file modified locally
- **WHEN** a file exists in the previous install archive
- **AND** that file is absent from the new template set
- **AND** the current local file differs from the previous original content
- **THEN** the local file is preserved
- **AND** the updater does not delete user changes

#### Scenario: Parent directories are preserved
- **WHEN** a removed upstream file is deleted during update
- **THEN** only the file is removed
- **AND** parent directories are left untouched
