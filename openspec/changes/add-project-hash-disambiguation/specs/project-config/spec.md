## ADDED Requirements

### Requirement: Project Path Hash Calculation
The system SHALL calculate a SHA256 hash of the full project path to uniquely identify projects with the same basename.

#### Scenario: Hash from MCP roots
- **WHEN** project path is available from MCP `list/roots`
- **THEN** extract full path from file URI
- **AND** calculate SHA256 hash of the absolute path
- **AND** generate 8-character short hash for key usage

#### Scenario: Hash from PWD fallback
- **WHEN** MCP roots are not available (CLI agents)
- **THEN** use current working directory as full path
- **AND** calculate SHA256 hash of the absolute path
- **AND** generate 8-character short hash for key usage

### Requirement: Hash-Based Project Keys
The system SHALL use `{name}-{short-hash}` format as project configuration keys to prevent conflicts.

#### Scenario: Unique key generation
- **WHEN** storing project configuration
- **THEN** generate key as `{project-name}-{hash[:8]}`
- **AND** store original name in `name` property
- **AND** store full hash in `hash` property

#### Scenario: Multiple projects with same name
- **WHEN** two projects have the same basename but different paths
- **THEN** each project gets a unique key with different hash suffix
- **AND** both projects can coexist in configuration
- **AND** project resolution works correctly for both

### Requirement: Hash Verification
The system SHALL verify project hash matches current path during project resolution.

#### Scenario: Hash match verification
- **WHEN** resolving project by name
- **THEN** calculate current path hash
- **AND** compare with stored hash
- **AND** use project if hash matches

#### Scenario: Hash mismatch handling
- **WHEN** stored hash doesn't match current path
- **THEN** log warning about potential project move
- **AND** continue using project (allow for project moves)
- **AND** update hash on next configuration save

## MODIFIED Requirements

### Requirement: Project Configuration Structure
The project configuration SHALL store projects using hash-suffixed keys with name and hash properties for disambiguation.

#### Scenario: Configuration format
- **WHEN** project configuration is saved
- **THEN** projects are stored as dictionary with hash-suffixed keys
- **AND** each project contains `name` property with display name
- **AND** each project contains `hash` property with full SHA256 hash
- **AND** existing categories and collections are preserved

#### Scenario: Legacy configuration migration
- **WHEN** loading configuration with legacy format (name-only keys)
- **THEN** calculate hash for current project path
- **AND** migrate to hash-suffixed key format
- **AND** preserve all existing project data
- **AND** save migrated configuration automatically

### Requirement: Project Resolution by Name
The system SHALL resolve projects by display name while using hash-suffixed keys internally.

#### Scenario: Single project match
- **WHEN** user specifies project name
- **AND** only one project exists with that name
- **THEN** resolve to that project regardless of hash suffix

#### Scenario: Multiple project matches
- **WHEN** user specifies project name
- **AND** multiple projects exist with that name
- **THEN** resolve using current path hash verification
- **AND** select project with matching hash
- **AND** create new project if no hash matches
