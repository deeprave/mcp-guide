## ADDED Requirements

### Requirement: Export Tracking Storage

The system SHALL store export tracking metadata in project configuration as a dict mapping (expression, pattern) tuple to export metadata.

Each export entry SHALL contain:
- Key: `(expression, pattern)` tuple (pattern is None if not provided)
- Value: `path` (export destination), `metadata_hash` (CRC32 hash of file metadata)

The metadata hash SHALL be computed from sorted file metadata entries in format `category:filename:mtime`, concatenated with `|` separator, using CRC32 algorithm formatted as 8 hex characters.

#### Scenario: Track successful export
- **WHEN** `export_content` completes successfully
- **THEN** upsert export entry with (expression, pattern) as key and computed metadata hash

#### Scenario: Re-export same expression with different pattern
- **WHEN** exporting same expression with different pattern
- **THEN** create separate tracking entry

### Requirement: Staleness Detection via Metadata Hash

The system SHALL detect when exported content is unchanged by comparing metadata hashes.

Detection SHALL:
- Gather files for the expression/pattern
- Compute metadata hash from gathered files
- Compare with stored hash from previous export
- Content is stale if hashes match

The metadata hash SHALL detect changes from:
- File modifications (mtime changes)
- Files added (new entries in hash input)
- Files deleted (missing entries in hash input)
- Pattern changes (different files match)
- Collection membership changes (different categories)
- Category configuration changes (affects file discovery)

#### Scenario: Content unchanged since export
- **WHEN** computed metadata hash equals stored hash
- **THEN** return "already exported" message with export path

#### Scenario: Content changed since export
- **WHEN** computed metadata hash differs from stored hash
- **THEN** proceed with normal export

#### Scenario: No previous export
- **WHEN** (expression, pattern) tuple not in export tracking
- **THEN** proceed with normal export

#### Scenario: File added with old mtime
- **WHEN** file with old mtime added to category
- **THEN** metadata hash changes (new filename entry) and export proceeds

### Requirement: export_content Tool

The system SHALL provide an `export_content` tool that exports rendered content to files for knowledge indexing.

Arguments:
- `expression` (required, string): Content expression
- `path` (required, string): Export destination path
- `pattern` (optional, string): Glob pattern filter
- `force` (optional, boolean): Override staleness check (default: false)

The tool SHALL:
- Check export tracking for matching (expression, pattern) tuple
- Gather files and compute metadata hash
- If stored hash matches computed hash, return "already exported" message
- If `force=true`, bypass staleness check
- On successful export, upsert tracking entry with computed metadata hash

#### Scenario: Export with unchanged content
- **WHEN** content previously exported and metadata hash unchanged
- **THEN** return message "Content for '{expression}' already exported to {path}. Use force=True to overwrite or if file is missing."

#### Scenario: Export with force flag
- **WHEN** `force=true` provided
- **THEN** bypass staleness check and export content

#### Scenario: Export with changed content
- **WHEN** metadata hash differs from stored hash
- **THEN** export content and update tracking metadata

#### Scenario: First export
- **WHEN** (expression, pattern) tuple not previously exported
- **THEN** export content and create tracking entry
