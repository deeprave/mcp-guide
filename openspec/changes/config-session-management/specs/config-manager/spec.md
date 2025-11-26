# Config Manager Specification

**JIRA**: MG-22
**Epic**: MG-18 - MCP Guide Architectural Reboot

## Purpose

Provide singleton ConfigManager for atomic YAML config file operations with file locking.

## ADDED Requirements

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

### Requirement: Constructor Injection for Testing
The system SHALL support config_dir parameter for test isolation.

#### Scenario: Test isolation
- WHEN ConfigManager is created with config_dir parameter
- THEN config file is located in specified directory
- AND production config is not accessed
- AND tests can use temporary directories

## Technical Details

### Singleton Pattern
- Async factory method: `await ConfigManager.get_instance()`
- Class-level lock acquired BEFORE checking instance
- Single instance per process
- Direct instantiation blocked: `ConfigManager()` raises RuntimeError

### File Locking
- Custom async file locking implementation (matches mcp-server-guide)
- Lock file: `{config_file}.lock`
- Stale lock timeout: 10 minutes
- PID and hostname tracking for cross-process/cross-host detection
- Cross-platform hostname detection (Windows and Unix)
- Exclusive locks for write operations

### YAML Format
```yaml
projects:
  project-name:
    name: project-name
    categories: [...]
    collections: [...]
    created_at: 2025-11-26T10:00:00
    updated_at: 2025-11-26T10:00:00
```

### Async Safety
- Singleton initialization uses asyncio.Lock
- Lock acquired BEFORE checking instance existence
- File operations protected by file locks
- No shared mutable state

## Dependencies
- Custom file locking (mcp_guide.file_lock)
- PyYAML for serialization
- mcp_guide.config_paths for default paths
- mcp_guide.models for Project model
