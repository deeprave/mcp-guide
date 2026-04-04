## MODIFIED Requirements
### Requirement: Switch Current Project
The system SHALL provide a tool to switch to a different project by name or full path.

#### Scenario: Switch to existing project
- **WHEN** user calls `set_current_project` with an existing project name
- **THEN** load that project's configuration and set it as current

#### Scenario: Create new project
- **WHEN** user calls `set_current_project` with a non-existent project name
- **THEN** create new project with default categories and set it as current

#### Scenario: Invalid project name
- **WHEN** user calls `set_current_project` with invalid characters or empty name
- **THEN** return error with type `invalid_name`

#### Scenario: Full path provided
- **WHEN** user calls `set_current_project` with an absolute filesystem path
- **THEN** the basename of the path SHALL be used as the project name
- **AND** the session roots SHALL be updated with the provided path
- **AND** `resolve_project_path()` SHALL return the provided directory

#### Scenario: File URI provided
- **WHEN** user calls `set_current_project` with a `file://` URI
- **THEN** the URI prefix SHALL be stripped and treated as an absolute path

#### Scenario: Relative path rejected
- **WHEN** user calls `set_current_project` with a relative path containing separators
- **THEN** return error with type `invalid_name`
- **AND** the error message SHALL indicate an absolute path is required

#### Scenario: Path traversal rejected
- **WHEN** user calls `set_current_project` with a path containing `..` components
- **THEN** return error with type `invalid_name`
- **AND** the error message SHALL indicate traversals are not permitted

### Requirement: Result Pattern Compliance
All project management tools SHALL return responses using the Result pattern.

#### Scenario: Unbound project error
- **WHEN** any tool requires a bound project and the session is unbound
- **THEN** return a consistent static `RESULT_NO_PROJECT` error
- **AND** the error SHALL include an instruction telling the agent to call `set_project` with the project path or name
