# filesystem-interaction Specification

## Purpose

Provides secure, bidirectional filesystem interaction between MCP server and agent using sampling requests, enabling the server to discover and read files from the agent's filesystem while maintaining strict security boundaries.

## MODIFIED Requirements

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

### Requirement: Sampling-Based File Reading
The system SHALL request file contents from the agent using MCP sampling requests.

#### Scenario: Read file content
- **WHEN** FilesystemBridge.read_file(path) is called
- **THEN** creates sampling request with prompt to read file at path
- **AND** path is validated against security policy before request
- **AND** agent provides file content via guide_cache_file tool
- **AND** content is stored in server-side cache
- **AND** returns file content as string

#### Scenario: Read file with encoding
- **WHEN** read_file is called with specific encoding
- **THEN** agent reads file with specified encoding
- **AND** encoding errors are handled gracefully
- **AND** fallback encodings are attempted if specified encoding fails

#### Scenario: Read binary file
- **WHEN** read_file is called with binary=True
- **THEN** agent provides base64-encoded content
- **AND** server decodes content to bytes
- **AND** returns binary data

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

### Requirement: File Content Caching
The system SHALL cache file contents to minimize redundant sampling requests.

#### Scenario: Cache file content
- **WHEN** agent provides file content via guide_cache_file
- **THEN** FileCache stores content with path as key
- **AND** stores file metadata (size, mtime, encoding)
- **AND** updates cache statistics

#### Scenario: Cache hit
- **WHEN** read_file is called for cached file
- **AND** cache entry is valid (not expired)
- **THEN** returns cached content without sampling request
- **AND** increments cache hit counter

#### Scenario: Cache miss
- **WHEN** read_file is called for uncached file
- **THEN** initiates sampling request to agent
- **AND** caches response for future requests
- **AND** increments cache miss counter

#### Scenario: Cache invalidation by modification time
- **WHEN** read_file is called for cached file
- **AND** file modification time is newer than cache entry
- **THEN** cache entry is invalidated
- **AND** fresh content is requested from agent
- **AND** cache is updated with new content

#### Scenario: Cache size management
- **WHEN** cache size exceeds configured limit
- **THEN** LRU (least recently used) entries are evicted
- **AND** eviction continues until size is below limit
- **AND** eviction statistics are tracked

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

#### Scenario: guide_cache_file tool
- **WHEN** agent calls guide_cache_file(path, content)
- **THEN** validates path against security policy
- **AND** stores content in FileCache
- **AND** returns success result with cache statistics
- **AND** rejects invalid paths with security error

#### Scenario: Batch file caching
- **WHEN** agent calls guide_cache_file with multiple files
- **THEN** validates all paths before caching any
- **AND** caches all files atomically
- **AND** returns batch operation statistics
- **AND** rolls back on any validation failure
