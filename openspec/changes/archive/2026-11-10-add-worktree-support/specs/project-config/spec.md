## MODIFIED Requirements

### Requirement: Project Configuration Structure

The project configuration SHALL store projects using hash-suffixed keys with name and hash properties for disambiguation. Persisted `allowed_write_paths` SHALL contain only user-added static paths; runtime defaults SHALL be derived for each active session and omitted from saved configuration.

#### Scenario: Configuration format

- **WHEN** project configuration is saved
- **THEN** projects are stored as dictionary with hash-suffixed keys
- **AND** each project contains `name` property with display name
- **AND** each project contains `hash` property with full SHA256 hash
- **AND** existing categories and collections are preserved
- **AND** runtime default write paths are omitted from the saved config

#### Scenario: Legacy configuration migration

- **WHEN** loading configuration with legacy format (name-only keys)
- **THEN** calculate hash for current project path
- **AND** migrate to hash-suffixed key format
- **AND** preserve all existing project data
- **AND** save migrated configuration automatically

#### Scenario: Default write paths not stored

- **WHEN** a project's saved `allowed_write_paths` contains only runtime defaults
- **THEN** the field is omitted from the serialized YAML
- **AND** on load, the defaults are derived for the active session

#### Scenario: Static write paths persist

- **WHEN** a user adds a non-default write path
- **THEN** that path is retained in `allowed_write_paths`
- **AND** survives configuration save and load
