# filesystem-interaction Specification

## Purpose
TBD - created by archiving change agent-server-filesystem-interaction. Update Purpose after archive.
## Requirements
### Requirement: Sampling-Based Directory Listing
The system SHALL request directory listings from the agent using MCP sampling requests.

#### Scenario: List directory contents
- **WHEN** FilesystemBridge.list_directory(path) is called
- **THEN** creates sampling request with prompt to list files in path
- **AND** agent responds with list of files and directories
- **AND** results are validated against security policy
- **AND** returns list of PathInfo objects with name, type, and metadata

#### Scenario: Recursive directory listing
- **WHEN** FilesystemBridge.list_directory(path, recursive=True) is called
- **THEN** agent provides nested directory structure
- **AND** all paths are validated against security policy
- **AND** returns hierarchical PathInfo tree

#### Scenario: Directory listing with filters
- **WHEN** list_directory is called with pattern filter
- **THEN** agent filters results by glob pattern
- **AND** only matching files are returned
- **AND** filtering happens on agent side for efficiency

### Requirement: Path Validation and Security
The system SHALL validate all filesystem paths against security policy before operations.

#### Scenario: Allowed path access
- **WHEN** operation requested on path within allowed directories
- **THEN** PathValidator.validate(path) returns normalized path
- **AND** operation proceeds normally

#### Scenario: Disallowed path access
- **WHEN** operation requested on path outside allowed directories
- **THEN** PathValidator.validate(path) raises SecurityError
- **AND** operation is blocked
- **AND** security audit log entry is created

#### Scenario: Path traversal prevention
- **WHEN** path contains parent directory references (..)
- **THEN** path is normalized and validated against allowed directories
- **AND** traversal outside allowed paths raises SecurityError
- **AND** absolute paths are resolved relative to project root

#### Scenario: Symbolic link validation
- **WHEN** path is a symbolic link
- **THEN** link target is resolved and validated
- **AND** link targets outside allowed paths are rejected
- **AND** circular links are detected and rejected

### Requirement: Security Policy Configuration
The system SHALL provide configurable security policy for filesystem access.

#### Scenario: Default allowed paths
- **WHEN** SecurityPolicy is initialized without configuration
- **THEN** uses default allowed paths: docs/, src/, tests/, .guide/, .todo/
- **AND** all other paths are denied by default

#### Scenario: Project-specific allowed paths
- **WHEN** project configuration includes filesystem.allowed_paths
- **THEN** SecurityPolicy uses configured allowed paths
- **AND** validates all configured paths exist
- **AND** logs warning for non-existent paths

#### Scenario: Path normalization
- **WHEN** allowed paths are configured
- **THEN** paths are normalized to absolute paths
- **AND** trailing slashes are removed
- **AND** paths are resolved relative to project root

### Requirement: Error Handling and Fallbacks
The system SHALL provide clear error handling for filesystem operations.

#### Scenario: File not found
- **WHEN** requested file does not exist
- **THEN** agent returns file not found error
- **AND** error is propagated to caller with clear message
- **AND** operation fails gracefully without caching

#### Scenario: Permission denied
- **WHEN** agent lacks permission to read file
- **THEN** agent returns permission denied error
- **AND** error is logged with security context
- **AND** operation fails with appropriate error message

#### Scenario: Sampling request timeout
- **WHEN** sampling request exceeds timeout
- **THEN** operation fails with timeout error
- **AND** partial results are discarded
- **AND** cache is not updated

#### Scenario: Unsupported client fallback
- **WHEN** MCP client does not support sampling requests
- **THEN** FilesystemBridge detects lack of support
- **AND** returns clear error message indicating limitation
- **AND** suggests alternative approaches (resources, manual file provision)

### Requirement: Audit Logging
The system SHALL log all filesystem operations for security audit.

#### Scenario: Operation audit log
- **WHEN** filesystem operation is performed
- **THEN** log entry includes operation type, path, timestamp, and result
- **AND** log level is TRACE for successful operations
- **AND** log level is WARNING for security violations

#### Scenario: Security violation logging
- **WHEN** path validation fails
- **THEN** log entry includes attempted path, violation type, and stack trace
- **AND** log entry includes client context if available
- **AND** repeated violations are tracked

### Requirement: Integration with MCP Tools
The system SHALL provide MCP tools for agent-server filesystem interaction.

#### Scenario: send_file_content tool
- **WHEN** agent calls send_file_content(path, content)
- **THEN** path is treated as an opaque identifier and is not validated as a filesystem path
- **AND** a missing or blank path is rejected as a validation error
- **AND** content is dispatched as an `FS_FILE_CONTENT` Session event
- **AND** the call returns a success result

#### Scenario: Batch file delivery
- **WHEN** agent calls send_file_content for multiple files
- **THEN** each call treats path as an opaque identifier
- **AND** each successful call dispatches one Session event
- **AND** a missing or blank path does not dispatch that file

#### Scenario: guide_cache_file tool
- **WHEN** agent would previously call guide_cache_file(path, content)
- **THEN** that tool SHALL NOT be provided
- **AND** the agent SHALL use send_file_content instead
- **AND** content is dispatched as an `FS_FILE_CONTENT` Session event rather than stored in FileCache

#### Scenario: Batch file caching
- **WHEN** agent would previously batch-cache files through guide_cache_file
- **THEN** that batch cache tool SHALL NOT be provided
- **AND** each file SHALL be delivered through send_file_content
- **AND** a missing or blank path SHALL NOT dispatch that file
