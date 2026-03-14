# Project Tools Specification Delta

## ADDED Requirements

### Requirement: Permission Path Management Tools

The system SHALL provide MCP tools for managing project permission paths without exposing configuration file structure to agents.

#### Scenario: Add write permission path
- **GIVEN** a project with existing write paths
- **WHEN** agent calls `add_permission_path` with `permission_type="write"` and `path="docs/"`
- **THEN** the path is added to `allowed_write_paths` in project config
- **AND** path is validated as relative
- **AND** duplicate paths are silently ignored
- **AND** success message is returned

#### Scenario: Add read permission path
- **GIVEN** a project with existing read paths
- **WHEN** agent calls `add_permission_path` with `permission_type="read"` and `path="/external/data"`
- **THEN** the path is added to `additional_read_paths` in project config
- **AND** path is validated as absolute and not a system directory
- **AND** duplicate paths are silently ignored
- **AND** success message is returned

#### Scenario: Remove permission path
- **GIVEN** a project with configured permission paths
- **WHEN** agent calls `remove_permission_path` with `permission_type` and `path`
- **THEN** the path is removed from the appropriate list if present
- **AND** no error occurs if path doesn't exist (silent success)
- **AND** success message is returned

#### Scenario: Invalid write path validation
- **GIVEN** an agent attempts to add a write path
- **WHEN** the path is absolute (e.g., `/absolute/path`)
- **THEN** validation error is returned
- **AND** config is not modified

#### Scenario: Invalid read path validation
- **GIVEN** an agent attempts to add a read path
- **WHEN** the path is relative or a system directory
- **THEN** validation error is returned
- **AND** config is not modified

### Requirement: Tool Arguments Structure

The system SHALL define typed argument classes for permission management tools following existing patterns.

#### Scenario: AddPermissionPathArgs structure
- **GIVEN** the `AddPermissionPathArgs` class
- **THEN** it SHALL inherit from `ToolArguments` (Pydantic BaseModel)
- **AND** it SHALL have `permission_type: Literal["read", "write"]` field with Field descriptor
- **AND** it SHALL have `path: str` field with Field descriptor
- **AND** fields SHALL include description metadata

#### Scenario: RemovePermissionPathArgs structure
- **GIVEN** the `RemovePermissionPathArgs` class
- **THEN** it SHALL inherit from `ToolArguments` (Pydantic BaseModel)
- **AND** it SHALL have `permission_type: Literal["read", "write"]` field with Field descriptor
- **AND** it SHALL have `path: str` field with Field descriptor
- **AND** fields SHALL include description metadata

### Requirement: Path Validation Reuse

The system SHALL reuse existing path validation logic from `Project` model validators.

#### Scenario: Write path validation reuse
- **GIVEN** the `add_permission_path` tool for write paths
- **WHEN** validating a write path
- **THEN** it SHALL use the same validation as `Project.validate_allowed_write_paths`
- **AND** enforce relative paths
- **AND** support both files (no trailing slash) and directories (trailing slash)
- **AND** use `validate_directory_path` for security checks

#### Scenario: Read path validation reuse
- **GIVEN** the `add_permission_path` tool for read paths
- **WHEN** validating a read path
- **THEN** it SHALL use the same validation as `Project.validate_additional_read_paths`
- **AND** enforce absolute paths
- **AND** check against system directories using `is_system_directory`

## Cross-References

- **Related Spec**: `help-template-system` - Permission command templates use these tools
- **Related Code**: `src/mcp_guide/models/project.py` - Validation logic source
- **Related Code**: `src/mcp_guide/tools/tool_project.py` - Tool implementation location
