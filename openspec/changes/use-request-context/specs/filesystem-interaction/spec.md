## REMOVED Requirements

### Requirement: File Content Caching
**Reason**: Agent-supplied file content is dispatched as Session filesystem events. A separate `FileCache` is not used.
**Migration**: Use `send_file_content`; content is carried on `FS_FILE_CONTENT` events rather than stored in a cache.

### Requirement: Sampling-Based File Reading
**Reason**: There is no `read_file` tool or `FilesystemBridge`. File content arrives through `send_file_content`. A later change may restore sampling-based reads in a different shape.
**Migration**: Deliver file content with `send_file_content`; do not specify a `read_file` contract here.

## MODIFIED Requirements

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
