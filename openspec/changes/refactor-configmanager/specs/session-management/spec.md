## MODIFIED Requirements

### Requirement: Session Configuration Management
The Session class SHALL fully encapsulate configuration management and provide controlled access to project configuration operations.

#### Scenario: Session creation with config directory
- **WHEN** a Session is created with a custom config directory
- **THEN** the Session SHALL create and manage its own internal ConfigManager instance
- **AND** the ConfigManager SHALL use the specified config directory

#### Scenario: Session creation without config directory
- **WHEN** a Session is created without specifying a config directory
- **THEN** the Session SHALL create and manage its own internal ConfigManager instance
- **AND** the ConfigManager SHALL use the default system config directory

#### Scenario: Configuration operations through Session
- **WHEN** configuration operations are needed (get project, save project, etc.)
- **THEN** all operations SHALL be performed through the Session's public interface
- **AND** direct access to ConfigManager SHALL NOT be available outside Session

### Requirement: Session Constructor Interface
The Session class constructor SHALL accept configuration parameters as keyword-only arguments with underscore prefixes for test-related parameters.

#### Scenario: Session instantiation with test configuration
- **WHEN** creating a new Session instance for testing
- **THEN** the constructor SHALL accept `project_name` as positional argument and `_config_dir_for_tests` as keyword-only argument
- **AND** test-related parameters SHALL be keyword-only and prefixed with underscore

#### Scenario: Session instantiation for production
- **WHEN** creating a new Session instance for production use
- **THEN** the constructor SHALL accept only `project_name` parameter
- **AND** the Session SHALL use default system configuration

## ADDED Requirements

### Requirement: ConfigManager Singleton Pattern
The ConfigManager SHALL be implemented as a class-level singleton within Session that can be reconfigured for different environments.

#### Scenario: ConfigManager singleton creation
- **WHEN** the first Session instance is created
- **THEN** a class-level ConfigManager singleton SHALL be created
- **AND** subsequent Session instances SHALL reuse the same ConfigManager instance

#### Scenario: ConfigManager reconfiguration for tests
- **WHEN** a Session is created with `_config_dir_for_tests` parameter
- **THEN** the existing ConfigManager singleton SHALL be reconfigured to use the test directory
- **AND** no temporary ConfigManager instances SHALL be created

#### Scenario: Concurrent ConfigManager access
- **WHEN** multiple async operations access ConfigManager simultaneously
- **THEN** access SHALL be properly synchronized with async locking
- **AND** ConfigManager state SHALL remain consistent

### Requirement: Project Key Tracking
The Session SHALL maintain the current project key (including hash suffix) separately from Project data.

#### Scenario: Project key storage
- **WHEN** a project is loaded from configuration
- **THEN** the Session SHALL store the project key (with hash suffix) as an instance variable
- **AND** the project key SHALL be used for subsequent save operations

#### Scenario: Project key usage in operations
- **WHEN** saving project configuration
- **THEN** the Session SHALL use the stored project key for file operations
- **AND** the project key SHALL NOT be stored within the Project data structure

### Requirement: Legacy Project Migration Optimization
Legacy project migration SHALL be performed efficiently and only when necessary.

#### Scenario: Legacy project detection
- **WHEN** loading a project configuration
- **THEN** legacy format SHALL be detected early in the loading process
- **AND** migration SHALL only be triggered for actual legacy projects

#### Scenario: One-time migration execution
- **WHEN** a legacy project is detected
- **THEN** migration SHALL be performed exactly once
- **AND** the migrated project SHALL be immediately saved to prevent re-migration

### Requirement: Session Factory Function Updates
Session factory functions SHALL use keyword-only parameters for test configuration and leverage the ConfigManager singleton.

#### Scenario: get_or_create_session with test configuration
- **WHEN** `get_or_create_session()` is called with test configuration
- **THEN** the function SHALL accept `_config_dir_for_tests` as keyword-only parameter
- **AND** the function SHALL reconfigure the existing ConfigManager singleton

#### Scenario: Session parameter forwarding
- **WHEN** session factory functions need to customize configuration
- **THEN** test-related parameters SHALL be keyword-only with underscore prefixes
- **AND** ConfigManager reconfiguration SHALL be handled through the singleton pattern

## MODIFIED Requirements

### Requirement: Test Configuration Isolation
Tests SHALL achieve configuration isolation through Session constructor parameters rather than ConfigManager injection.

#### Scenario: Integration test isolation
- **WHEN** integration tests need isolated configuration environments
- **THEN** tests SHALL create Session instances with `_config_dir_for_tests` keyword parameter
- **AND** tests SHALL NOT create or inject ConfigManager instances directly

#### Scenario: Concurrent test execution
- **WHEN** multiple tests run concurrently with different configurations
- **THEN** each test SHALL reconfigure the ConfigManager singleton appropriately
- **AND** configuration isolation SHALL be maintained through proper async locking
