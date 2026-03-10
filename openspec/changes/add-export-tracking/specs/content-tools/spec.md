## ADDED Requirements

### Requirement: Export Tracking Storage

The system SHALL store export tracking metadata in project configuration as a dict mapping (expression, pattern) tuple to export metadata.

Each export entry SHALL contain:
- Key: `(expression, pattern)` tuple (pattern is None if not provided)
- Value: `path` (export destination), `mtime` (Unix timestamp)

#### Scenario: Track successful export
- **WHEN** `export_content` completes successfully
- **THEN** upsert export entry with (expression, pattern) as key

#### Scenario: Re-export same expression with different pattern
- **WHEN** exporting same expression with different pattern
- **THEN** create separate tracking entry

### Requirement: Staleness Detection

The system SHALL detect when exported content is unchanged since last export.

Detection SHALL:
- Pass `updated_since` timestamp to file discovery
- Filter files where `mtime <= updated_since` during traversal
- Return true if any file has `mtime > updated_since`

#### Scenario: Content unchanged since export
- **WHEN** all discovered files have `mtime <= updated_since`
- **THEN** return "already available" message with export path and age

#### Scenario: Content changed since export
- **WHEN** any discovered file has `mtime > updated_since`
- **THEN** proceed with normal export

#### Scenario: No previous export
- **WHEN** (expression, pattern) tuple not in export tracking
- **THEN** proceed with normal export

## MODIFIED Requirements

### Requirement: export_content Tool

The system SHALL provide an `export_content` tool that exports rendered content to files for knowledge indexing.

Arguments:
- `expression` (required, string): Content expression
- `path` (required, string): Export destination path
- `pattern` (optional, string): Glob pattern filter
- `force` (optional, boolean): Override staleness check (default: false)

The tool SHALL:
- Check export tracking for matching (expression, pattern) tuple
- If found and content unchanged, return "already available" message
- If `force=true`, pass `updated_since=None` to bypass staleness check
- On successful export, upsert tracking entry with (expression, pattern) as key

#### Scenario: Export with unchanged content
- **WHEN** content previously exported and unchanged
- **THEN** return message "Content already exported to {path} (exported {age} ago, no changes detected)"

#### Scenario: Export with force flag
- **WHEN** `force=true` provided
- **THEN** bypass staleness check and export content

#### Scenario: Export with changed content
- **WHEN** content changed since last export
- **THEN** export content and update tracking metadata

#### Scenario: First export
- **WHEN** (expression, pattern) tuple not previously exported
- **THEN** export content and create tracking entry

#### Scenario: Agent-specific message
- **WHEN** agent is kiro-cli or q-dev
- **THEN** append "and indexed in knowledge base" to already-available message
