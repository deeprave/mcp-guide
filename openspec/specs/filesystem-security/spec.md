# filesystem-security Specification

## Purpose
TBD - created by archiving change agent-server-filesystem-interaction. Update Purpose after archive.
## Requirements
### Requirement: Read/Write Security Policy Separation
The system SHALL validate filesystem paths with separate read and write permissions using ReadWriteSecurityPolicy.

#### Scenario: Read access for relative paths
- **WHEN** read operation is requested on relative path
- **THEN** ReadWriteSecurityPolicy.validate_read_path() assumes path is allowed
- **AND** path is normalized and validated for traversal attempts
- **AND** operation proceeds normally (project root validation deferred)

#### Scenario: Read access within project root (when known)
- **WHEN** read operation is requested and project root is set
- **THEN** relative paths are resolved against project root
- **AND** access is allowed for paths within project boundaries
- **AND** operation proceeds normally

#### Scenario: Write access restricted to relative allowed paths
- **WHEN** write operation is requested on relative path
- **THEN** path must be within configured allowed_write_paths (relative)
- **AND** ReadWriteSecurityPolicy.validate_write_path() validates against allowed_write_paths
- **AND** operation proceeds if path matches allowed pattern

#### Scenario: Write access blocked outside allowed paths
- **WHEN** write operation is requested outside allowed_write_paths configuration
- **THEN** ReadWriteSecurityPolicy.validate_write_path() raises SecurityError
- **AND** operation is blocked
- **AND** security audit log entry is created

#### Scenario: Write access to temporary directories
- **WHEN** write operation is requested to safe temporary directory
- **THEN** is_safe_temp_path() validates path as safe temporary location
- **AND** ReadWriteSecurityPolicy.validate_write_path() allows access
- **AND** operation proceeds without checking allowed_write_paths

### Requirement: Project Root Injection
The system SHALL support optional project root injection for path resolution without requiring it upfront.

#### Scenario: Security policy without project root
- **WHEN** ReadWriteSecurityPolicy is initialized without project root
- **THEN** read operations assume relative paths are allowed
- **AND** write operations validate against relative allowed_write_paths
- **AND** absolute additional_read_paths are validated independently

#### Scenario: Project root injection after discovery
- **WHEN** set_project_root() is called with discovered project root
- **THEN** subsequent path validations use project root for resolution
- **AND** relative paths are resolved against project root
- **AND** existing validation rules continue to apply

#### Scenario: Read operations before project root known
- **WHEN** read operation is requested before project root is set
- **THEN** relative paths are assumed to be valid
- **AND** absolute additional_read_paths are validated normally
- **AND** operation proceeds without project root dependency

### Requirement: System Directory Blacklist
The system SHALL maintain a blacklist of dangerous system directories that cannot be accessed for read operations.

#### Scenario: System directory detection
- **WHEN** path validation is performed on system directory
- **THEN** is_system_directory() returns true for blacklisted paths
- **AND** blacklist includes /etc, /usr/bin, /usr/sbin, /bin, /sbin, /boot, /dev, /proc, /sys, /root
- **AND** blacklist includes SSH key directories (/home/*/.ssh, /Users/*/.ssh)
- **AND** blacklist includes Windows system directories (C:\Windows, C:\Program Files)

#### Scenario: System directory access blocked
- **WHEN** additional_read_paths includes system directory
- **THEN** project configuration validation raises ValueError
- **AND** error message indicates system directory is not allowed
- **AND** configuration is rejected

### Requirement: Additional Read Paths Configuration
The system SHALL support absolute paths for additional read-only access outside project root.

#### Scenario: Absolute path validation
- **WHEN** additional_read_paths is configured in project
- **THEN** all paths must be absolute paths
- **AND** relative paths raise ValueError during validation
- **AND** paths are validated against system directory blacklist

#### Scenario: Additional read path access
- **WHEN** read operation is requested on configured additional path
- **THEN** access is granted if path is within additional_read_paths
- **AND** subdirectories of additional paths are accessible
- **AND** path traversal outside additional paths is blocked

#### Scenario: Additional read paths persistence
- **WHEN** project configuration is saved
- **THEN** additional_read_paths are included in configuration file
- **AND** paths are stored as absolute paths
- **AND** configuration can be loaded and validated correctly

### Requirement: Temporary Directory Write Support
The system SHALL allow write operations to safe temporary directories regardless of allowed_write_paths configuration.

#### Scenario: Safe temporary directory identification
- **WHEN** is_safe_temp_path() is called with path
- **THEN** returns True if path contains "tmp" or "temp" directory components
- **AND** returns True if path starts with resolved TMPDIR, TEMP, or TMP environment variables
- **AND** returns True for standard cache directories (/.cache/)
- **AND** returns False for non-temporary paths

#### Scenario: Temporary directory write access
- **WHEN** write operation is requested to temporary directory
- **THEN** is_safe_temp_path() validates path as safe temporary location
- **AND** ReadWriteSecurityPolicy.validate_write_path() allows access
- **AND** operation proceeds without checking allowed_write_paths

#### Scenario: Temporary directory path resolution
- **WHEN** temporary directory path contains environment variables or ~ expansion
- **THEN** path is expanded to absolute path before validation
- **AND** expanded path is validated as safe temporary location
- **AND** access is granted if path resolves to safe temporary directory

