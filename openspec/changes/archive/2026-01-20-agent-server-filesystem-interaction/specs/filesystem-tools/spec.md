# filesystem-tools Specification

## Purpose

Provides MCP tools that enable secure agent-server filesystem interaction, allowing agents to provide file contents and directory listings to the server while maintaining strict security boundaries.

## ADDED Requirements

### Requirement: guide_cache_file Tool
The system SHALL provide guide_cache_file tool for agents to cache file contents on the server.

#### Scenario: Cache single file
- **WHEN** agent calls guide_cache_file with path and content
- **THEN** validates path against security policy
- **AND** normalizes path to absolute path
- **AND** stores content in server-side cache
- **AND** stores metadata (size, timestamp, encoding)
- **AND** returns success result with cache key

#### Scenario: Cache with metadata
- **WHEN** guide_cache_file includes optional metadata (mtime, encoding, size)
- **THEN** stores metadata alongside content
- **AND** uses metadata for cache invalidation decisions
- **AND** returns metadata in success result

#### Scenario: Security policy violation
- **WHEN** path is outside allowed directories
- **THEN** rejects operation with SecurityError
- **AND** returns failure result with clear error message
- **AND** logs security violation
- **AND** does not cache content

#### Scenario: Overwrite existing cache entry
- **WHEN** guide_cache_file called for already-cached path
- **THEN** overwrites existing cache entry
- **AND** updates modification timestamp
- **AND** increments cache update counter
- **AND** returns success with "updated" status

#### Scenario: Cache size limit exceeded
- **WHEN** caching content would exceed cache size limit
- **THEN** evicts LRU entries to make space
- **AND** proceeds with caching after eviction
- **AND** returns success with eviction statistics

### Requirement: guide_list_directory Tool
The system SHALL provide guide_list_directory tool for agents to provide directory listings.

#### Scenario: List directory contents
- **WHEN** server requests directory listing
- **THEN** agent calls guide_list_directory with path and file list
- **AND** validates path against security policy
- **AND** validates all listed paths against security policy
- **AND** stores directory listing in cache
- **AND** returns success result

#### Scenario: Include file metadata
- **WHEN** guide_list_directory includes file metadata
- **THEN** stores metadata (size, mtime, type) for each file
- **AND** metadata is available for subsequent operations
- **AND** metadata is used for cache invalidation

#### Scenario: Recursive listing
- **WHEN** guide_list_directory includes nested directories
- **THEN** validates entire directory tree
- **AND** stores hierarchical structure
- **AND** supports efficient tree traversal

#### Scenario: Filter by pattern
- **WHEN** guide_list_directory includes pattern parameter
- **THEN** only files matching pattern are accepted
- **AND** pattern is validated for safety
- **AND** invalid patterns are rejected

### Requirement: guide_read_file Tool
The system SHALL provide guide_read_file tool for agents to provide file contents.

#### Scenario: Read text file
- **WHEN** server requests file content
- **THEN** agent calls guide_read_file with path and content
- **AND** validates path against security policy
- **AND** stores content in cache
- **AND** returns success result with content hash

#### Scenario: Read binary file
- **WHEN** guide_read_file includes binary content (base64)
- **THEN** validates base64 encoding
- **AND** decodes and stores binary content
- **AND** preserves binary integrity
- **AND** returns success with content hash verification

#### Scenario: File encoding specification
- **WHEN** guide_read_file includes encoding parameter
- **THEN** stores encoding information with content
- **AND** uses encoding for subsequent operations
- **AND** validates encoding is supported

#### Scenario: Large file handling
- **WHEN** file content exceeds size threshold
- **THEN** accepts content in chunks
- **AND** assembles chunks in cache
- **AND** validates chunk integrity
- **AND** returns success after all chunks received

### Requirement: Tool Arguments Validation
The system SHALL validate all tool arguments using Pydantic models.

#### Scenario: Required arguments validation
- **WHEN** tool is called without required arguments
- **THEN** Pydantic validation fails
- **AND** returns clear error message indicating missing arguments
- **AND** operation does not proceed

#### Scenario: Type validation
- **WHEN** tool arguments have incorrect types
- **THEN** Pydantic validation fails with type error
- **AND** returns error message with expected and actual types
- **AND** operation does not proceed

#### Scenario: Path format validation
- **WHEN** path argument contains invalid characters
- **THEN** validation fails with format error
- **AND** returns error message with validation rules
- **AND** operation does not proceed

### Requirement: Tool Results
The system SHALL return structured results using Result[T] pattern.

#### Scenario: Success result with data
- **WHEN** tool operation succeeds
- **THEN** returns Result.ok(data)
- **AND** success field is True
- **AND** includes operation statistics (cache hits, file count, etc.)
- **AND** includes optional message for agent guidance

#### Scenario: Failure result with error
- **WHEN** tool operation fails
- **THEN** returns Result.failure(error, error_type)
- **AND** success field is False
- **AND** error field contains clear error message
- **AND** error_type indicates failure category (security, validation, system)
- **AND** includes instruction for agent on how to proceed

#### Scenario: Partial success with warnings
- **WHEN** tool operation completes with warnings
- **THEN** returns Result.ok(data)
- **AND** includes warnings field with list of issues
- **AND** message indicates partial success
- **AND** agent can decide whether to retry or accept result

### Requirement: Tool Documentation
The system SHALL provide comprehensive documentation for all tools.

#### Scenario: Tool description generation
- **WHEN** tool is registered with FastMCP
- **THEN** description includes purpose and usage
- **AND** description includes argument schema
- **AND** description includes examples
- **AND** description includes security notes

#### Scenario: Argument schema documentation
- **WHEN** ToolArguments.to_schema_markdown() is called
- **THEN** generates markdown with argument details
- **AND** includes argument types and constraints
- **AND** includes required/optional status
- **AND** includes default values

#### Scenario: Usage examples
- **WHEN** tool documentation is generated
- **THEN** includes practical usage examples
- **AND** shows successful operations
- **AND** shows error handling
- **AND** shows integration with filesystem operations

### Requirement: Tool Security
The system SHALL enforce security policies in all filesystem tools.

#### Scenario: Path validation on every call
- **WHEN** filesystem tool is called
- **THEN** validates all paths before any operation
- **AND** rejects invalid paths immediately
- **AND** logs security violations
- **AND** returns security error to agent

#### Scenario: Audit logging for all operations
- **WHEN** filesystem tool is invoked
- **THEN** logs operation with timestamp and context
- **AND** logs arguments (sanitized for security)
- **AND** logs result status
- **AND** logs any security violations

#### Scenario: Rate limiting consideration
- **WHEN** filesystem tools are called repeatedly
- **THEN** tracks call frequency per client
- **AND** logs warning for unusual patterns
- **AND** provides statistics for rate limiting decisions

### Requirement: Integration with FilesystemBridge
The system SHALL integrate filesystem tools with FilesystemBridge for cohesive operation.

#### Scenario: Cache synchronization
- **WHEN** guide_cache_file is called
- **THEN** FileCache is updated through FilesystemBridge
- **AND** cache statistics are synchronized
- **AND** cache eviction policies are respected

#### Scenario: Security policy consistency
- **WHEN** filesystem tools validate paths
- **THEN** uses same SecurityPolicy as FilesystemBridge
- **AND** validation results are consistent
- **AND** configuration changes apply to all components

#### Scenario: Error handling consistency
- **WHEN** filesystem operations fail
- **THEN** error handling is consistent with FilesystemBridge
- **AND** error messages follow same format
- **AND** error types use same enumeration