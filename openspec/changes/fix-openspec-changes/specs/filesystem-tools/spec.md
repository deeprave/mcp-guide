## MODIFIED Requirements

### Requirement: guide_list_directory Tool

The system SHALL provide guide_list_directory tool for agents to provide
validated directory listings and optional metadata about the listed directory.

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

#### Scenario: Include directory modification time
- **WHEN** guide_list_directory includes a directory mtime
- **THEN** includes the supplied value in the directory-listing event
- **AND** makes it available to task subscribers
- **AND** permits consumers to use it for cache invalidation

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
