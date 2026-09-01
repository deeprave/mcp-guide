# config-manager Specification

## Purpose
TBD - created by archiving change config-session-management. Update Purpose after archive.

## Requirements

### Requirement: Singleton Pattern
The system SHALL implement ConfigManager as an async-safe singleton.

#### Scenario: Single instance
- WHEN `await ConfigManager.get_instance()` is called multiple times
- THEN the same instance is returned
- AND initialization is protected by async lock
- AND lock is acquired BEFORE checking instance existence

### Requirement: Config File Management
The system SHALL manage a single YAML config file with atomic operations.

#### Scenario: Config file location
- WHEN config file path is requested
- THEN it uses XDG_CONFIG_HOME on Unix
- AND it uses APPDATA on Windows
- AND it defaults to `~/.config/mcp-guide/config.yaml` on Unix
- AND it defaults to `%APPDATA%/mcp-guide/config.yaml` on Windows

#### Scenario: File locking
- WHEN config file is accessed
- THEN a file lock is acquired
- AND operations are atomic
- AND lock is released after operation
- AND concurrent access is serialized

### Requirement: Project CRUD Operations
The system SHALL provide create, read, update, delete operations for projects.

#### Scenario: Get or create project
- WHEN `get_or_create_project_config(name)` is called
- THEN existing project is returned if it exists
- AND new project is created and saved if it doesn't exist
- AND file lock is held during operation

#### Scenario: Save project
- WHEN `save_project_config(project)` is called
- THEN project is serialized to YAML
- AND file is written atomically
- AND file lock is held during write

#### Scenario: List projects
- WHEN `list_projects()` is called
- THEN all project names are returned
- AND empty list is returned if no config exists

#### Scenario: Delete project
- WHEN `delete_project(name)` is called
- THEN project is removed from config
- AND config file is updated
- AND error is raised if project doesn't exist

#### Scenario: Rename project
- WHEN `rename_project(old_name, new_name)` is called
- THEN project is renamed in config
- AND config file is updated
- AND error is raised if old_name doesn't exist
- AND error is raised if new_name already exists

### Requirement: Project Configuration Model
The configuration system SHALL support project-specific feature flags with flexible value types.

#### Scenario: Project feature flags storage
- **WHEN** project configuration is loaded
- **THEN** include project_flags dict with FeatureValue types

#### Scenario: Default empty project flags
- **WHEN** new project is created
- **THEN** project_flags defaults to empty dict

#### Scenario: Project flag normalization before storage
- **WHEN** a project flag is set through the supported feature flag APIs
- **THEN** default or registered normalization SHALL run before the value is
  stored in project configuration
- **AND** canonical boolean values SHALL be persisted as booleans

### Requirement: Error Handling
The system SHALL provide clear error messages for config operations.

#### Scenario: Invalid project name
- WHEN operation uses invalid project name
- THEN ValueError is raised with clear message

#### Scenario: File system errors
- WHEN config file cannot be read/written
- THEN IOError is raised with clear message
- AND file lock is released

#### Scenario: YAML parsing errors
- WHEN config file contains invalid YAML
- THEN YAMLError is raised with clear message
- AND error includes file location

### Requirement: Global Configuration Model
The configuration system SHALL support global feature flags with flexible value types.

#### Scenario: Global feature flags storage
- **WHEN** global configuration is loaded
- **THEN** include feature_flags dict with FeatureValue types

#### Scenario: Default empty feature flags
- **WHEN** new configuration is created
- **THEN** feature_flags defaults to empty dict

#### Scenario: Global flag normalization before storage
- **WHEN** a global feature flag is set through the supported feature flag APIs
- **THEN** default or registered normalization SHALL run before the value is
- stored in global configuration
- **AND** canonical boolean values SHALL be persisted as booleans

### Requirement: Constructor Injection for Testing
The system SHALL support config_dir parameter for test isolation.

#### Scenario: Test isolation
- WHEN ConfigManager is created with config_dir parameter
- THEN config file is located in specified directory
- AND production config is not accessed
- AND tests can use temporary directories

### Requirement: Feature Flag Value Types
Feature flag values SHALL be restricted to supported types for consistency and validation.

The default supported value types for generic feature flags SHALL be boolean and
string values only.

Structured values such as `list[str]` and `dict[str, str | list[str]]` SHALL be
accepted only for flags that explicitly register a validator and normaliser that
support those shapes.

#### Scenario: Supported default value types
- **WHEN** a generic feature flag value is set
- **THEN** accept only boolean or string values by default

#### Scenario: Registered structured flag value
- **WHEN** a built-in flag with a registered validator is set to its supported
  structured value
- **THEN** the configuration system SHALL accept the value
- **AND** it SHALL use the registered flag-specific behavior

#### Scenario: Unsupported generic structured value
- **WHEN** a generic feature flag is set to a list or dictionary value without a
  registered structured validator
- **THEN** return validation error with the supported default types

### Requirement: Feature Flag Name Validation
Feature flag names SHALL follow project name validation rules with additional restrictions.

#### Scenario: Valid flag names
- **WHEN** flag name is validated
- **THEN** accept alphanumeric characters, hyphens, and underscores only

#### Scenario: Reject periods in flag names
- **WHEN** flag name contains periods
- **THEN** return validation error to avoid confusion with project syntax

#### Scenario: Name length validation
- **WHEN** flag name is validated
- **THEN** enforce same length restrictions as project names

### Requirement: Feature Flag Resolution
The system SHALL resolve feature flag values using project-specific → global → None hierarchy.

#### Scenario: Project flag takes precedence
- **WHEN** flag exists in both project and global configuration
- **THEN** return project-specific value

#### Scenario: Global flag fallback
- **WHEN** flag exists only in global configuration
- **THEN** return global value

#### Scenario: Flag not found
- **WHEN** flag does not exist in project or global configuration
- **THEN** return None

### Requirement: Absolute Docroot When The Config Key Is Missing
When a configuration file exists but `docroot` is absent, blank, or not a
string, the configuration service SHALL persist an absolute default beside that
configuration file. It SHALL NOT persist a current-working-directory-relative
path, and it SHALL NOT unpack packaged templates into the repository worktree
as a side effect of filling that key.

#### Scenario: Config file lacks a docroot key
- **WHEN** the configuration file is present and `docroot` is missing or blank
- **THEN** the service SHALL store an absolute path in the same directory as the
  configuration file's default docs location
- **AND** it SHALL NOT write a CWD-relative value such as `tests/fixtures/docs`

#### Scenario: First-run install uses a relative config directory
- **WHEN** first-run installation creates configuration because the file is
  missing
- **THEN** both the configuration directory and the installed docroot SHALL be
  stored as absolute paths
- **AND** the install SHALL NOT unpack templates into a git-tracked worktree
  path as a default

### Requirement: GuideRuntime Is The Sole ConfigManager Constructor
The process runtime SHALL construct the configuration service from the config
directory and docroot it is given. Application entry points, Sessions, and
feature-flag handlers SHALL NOT import or instantiate that configuration-service
class. Tests SHALL obtain a configuration service only by constructing a
process runtime.

#### Scenario: Server starts
- **WHEN** the MCP server application is constructed
- **THEN** it SHALL construct a process runtime with a config directory
- **AND** it SHALL NOT import or construct the configuration-service class

#### Scenario: Session needs project configuration
- **WHEN** a Session performs project CRUD, clone lookup, or registration
- **THEN** it SHALL obtain the configuration service from its process runtime
- **AND** the Session module SHALL NOT import the configuration-service class
