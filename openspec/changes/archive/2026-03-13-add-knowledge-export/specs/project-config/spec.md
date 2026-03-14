## MODIFIED Requirements

### Requirement: Project Configuration Structure
The project configuration SHALL store projects using hash-suffixed keys with name and hash properties for disambiguation.

#### Scenario: Configuration format
- **WHEN** project configuration is saved
- **THEN** projects are stored as dictionary with hash-suffixed keys
- **AND** each project contains `name` property with display name
- **AND** each project contains `hash` property with full SHA256 hash
- **AND** existing categories and collections are preserved
- **AND** `allowed_write_paths` is omitted from the saved config when it equals `DEFAULT_ALLOWED_WRITE_PATHS`

#### Scenario: Legacy configuration migration
- **WHEN** loading configuration with legacy format (name-only keys)
- **THEN** calculate hash for current project path
- **AND** migrate to hash-suffixed key format
- **AND** preserve all existing project data
- **AND** save migrated configuration automatically

#### Scenario: Default write paths not stored
- **WHEN** a project's `allowed_write_paths` equals `DEFAULT_ALLOWED_WRITE_PATHS`
- **THEN** the field is omitted from the serialized YAML
- **AND** on load, the default value is applied automatically by the model
