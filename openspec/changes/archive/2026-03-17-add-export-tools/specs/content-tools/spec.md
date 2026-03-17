## ADDED Requirements

### Requirement: list_exports Tool
The system SHALL provide a `list_exports` tool that returns a list of all tracked content exports with metadata. The tool accepts an `options` parameter (`list[str]`) that controls template rendering via `parse_options`.

#### Scenario: List all exports
- **WHEN** `list_exports` is called with no filter
- **THEN** all entries from `Project.exports` are returned as a JSON array
- **AND** each entry includes expression, pattern, path, exported_at timestamp, and stale indicator

#### Scenario: Filter by glob pattern
- **WHEN** `list_exports` is called with a glob pattern
- **THEN** only exports matching the glob (against expression, pattern, or path) are returned
- **AND** glob matching is case-insensitive

#### Scenario: Empty exports
- **WHEN** `list_exports` is called and no exports exist
- **THEN** an empty array is returned

#### Scenario: Formatted output via options
- **WHEN** `list_exports` is called with non-empty `options`
- **THEN** output is rendered via `_system/_exports-format.mustache`
- **AND** each option is parsed by `parse_options` into the template context
- **AND** truthy flags (e.g. `"verbose"`) become `True` in context
- **AND** key=value pairs (e.g. `"limit=10"`) become string values in context

#### Scenario: Raw JSON output
- **WHEN** `list_exports` is called with empty `options` (default)
- **THEN** raw JSON array is returned without template rendering

#### Scenario: Staleness detection
- **WHEN** `list_exports` computes staleness for an export
- **THEN** it resolves the expression/pattern to get current file list
- **AND** computes metadata_hash from current file mtimes
- **AND** compares to stored hash
- **AND** sets stale=true if hashes differ, stale=false if they match

#### Scenario: Missing export file
- **WHEN** an export's destination file does not exist or is not readable
- **THEN** exported_at is null
- **AND** stale indicator is "unknown"

### Requirement: parse_options Utility
The system SHALL provide a reusable `parse_options` function in `tool_result.py` that converts a list of display option strings into a template context dict.

#### Scenario: Truthy flag
- **WHEN** options list contains `"verbose"`
- **THEN** result dict contains `{"verbose": True}`

#### Scenario: Key=value pair
- **WHEN** options list contains `"limit=10"`
- **THEN** result dict contains `{"limit": "10"}`

#### Scenario: Mixed options
- **WHEN** options list contains `["verbose", "limit=10"]`
- **THEN** result dict contains `{"verbose": True, "limit": "10"}`

#### Scenario: Empty options
- **WHEN** options list is empty
- **THEN** result dict is empty

### Requirement: remove_export Tool
The system SHALL provide a `remove_export` tool that removes export tracking entries from `Project.exports`.

#### Scenario: Remove by exact match
- **WHEN** `remove_export` is called with expression and pattern
- **THEN** the entry with key `(expression, pattern)` is removed from `Project.exports`
- **AND** Result.ok is returned with confirmation message

#### Scenario: Remove expression-only export
- **WHEN** `remove_export` is called with expression and no pattern
- **THEN** the entry with key `(expression, None)` is removed
- **AND** Result.ok is returned

#### Scenario: Export not found
- **WHEN** `remove_export` is called with expression/pattern that doesn't exist
- **THEN** Result.failure is returned with error_type "not_found"
- **AND** message indicates the exact key that was not found

#### Scenario: File not deleted
- **WHEN** `remove_export` successfully removes tracking entry
- **THEN** the actual exported file is NOT deleted
- **AND** only the tracking entry is removed from `Project.exports`
