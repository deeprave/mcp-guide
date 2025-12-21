# guide-project-tools Specification

## Purpose
TBD - created by archiving change add-guide-project-tools. Update Purpose after archive.
## Requirements
### Requirement: Get Current Project Information
The `guide_get_project` tool SHALL return complete project configuration including categories, collections, and resolved project flags.

#### Scenario: Get complete project configuration
- GIVEN a project with categories, collections, and flags configured
- WHEN `guide_get_project(verbose=true)` is called
- THEN the response SHALL include:
  - Project name
  - Categories with their configuration
  - Collections with their configuration
  - Resolved project flags (global + project-specific)

#### Scenario: Get basic project information
- GIVEN a project configuration
- WHEN `guide_get_project(verbose=false)` is called
- THEN the response SHALL include project name and basic structure
- AND flags MAY be omitted for brevity

#### Scenario: Flag resolution
- GIVEN global feature flags and project-specific flags
- WHEN project flags are requested
- THEN the response SHALL include fully resolved flags
- AND project-specific flags SHALL override global flags where conflicts exist

### Requirement: Switch Current Project
The system SHALL provide a tool to switch to a different project by name.

#### Scenario: Switch to existing project
- **WHEN** user calls `set_current_project` with an existing project name
- **THEN** load that project's configuration and set it as current

#### Scenario: Create new project
- **WHEN** user calls `set_current_project` with a non-existent project name
- **THEN** create new project with default categories and set it as current

#### Scenario: Invalid project name
- **WHEN** user calls `set_current_project` with invalid characters or empty name
- **THEN** return error with type `invalid_name`

---

### Requirement: Clone Project Configuration
The system SHALL provide a tool to copy project configuration between projects.

#### Scenario: Clone to current project with merge
- **WHEN** user calls `clone_project` with source project and `merge=True`
- **THEN** merge source categories and collections into current project, overwriting conflicts

#### Scenario: Clone to current project with replace
- **WHEN** user calls `clone_project` with source project and `merge=False`
- **THEN** replace current project configuration entirely with source configuration

#### Scenario: Clone to specified project
- **WHEN** user calls `clone_project` with source and target project names
- **THEN** copy configuration to target project without changing current project

#### Scenario: Safeguard prevents destructive operation
- **WHEN** user calls `clone_project` with `merge=False` and target has existing configuration
- **THEN** return error unless `force=True` is specified

#### Scenario: Conflict detection in merge
- **WHEN** user calls `clone_project` with `merge=True` and conflicts exist
- **THEN** return warnings listing conflicting categories and collections

---

### Requirement: List All Projects
The system SHALL provide a tool to list all available projects.

#### Scenario: List project names only
- **WHEN** user calls `list_projects` with `verbose=False`
- **THEN** return list of project names

#### Scenario: List projects with full details
- **WHEN** user calls `list_projects` with `verbose=True`
- **THEN** return dictionary with project names as keys and full configuration as values

#### Scenario: No projects exist
- **WHEN** user calls `list_projects` and no projects are configured
- **THEN** return empty list or empty dictionary

---

### Requirement: Get Specific Project Details
The system SHALL provide a tool to retrieve details for a specific project by name.

#### Scenario: Get existing project details
- **WHEN** user calls `list_project` with an existing project name
- **THEN** return full project details including collections and categories

#### Scenario: Project not found
- **WHEN** user calls `list_project` with non-existent project name
- **THEN** return error with type `not_found`

---

### Requirement: Result Pattern Compliance
All project management tools SHALL return responses using the Result pattern.

#### Scenario: Successful operation
- **WHEN** any tool completes successfully
- **THEN** return `Result.ok()` with data in `value` field

#### Scenario: Failed operation
- **WHEN** any tool encounters an error
- **THEN** return `Result.failure()` with `error`, `error_type`, and optional `instruction` fields

---

### Requirement: Tool Self-Documentation
All project management tools SHALL be self-documenting via MCP schema.

#### Scenario: Tool description available
- **WHEN** MCP client queries tool information
- **THEN** tool description and purpose are visible

#### Scenario: Argument schema available
- **WHEN** MCP client queries tool arguments
- **THEN** argument names, types, defaults, and descriptions are visible

---

### Requirement: Cache Consistency
The system SHALL maintain consistency between configuration files and in-memory cache.

#### Scenario: Auto-reload after modification
- **WHEN** `clone_project` modifies the current project's configuration
- **THEN** automatically reload the project cache

#### Scenario: Session isolation
- **WHEN** multiple projects are accessed in different sessions
- **THEN** each session maintains its own isolated cache

