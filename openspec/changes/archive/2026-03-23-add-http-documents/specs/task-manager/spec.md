# Task Manager Specification

## ADDED Requirements

### Requirement: Document Handler Task
The system SHALL provide a background "document handler" task registered with the task manager.

The document handler task SHALL:
- Run periodically to check cached documents whose refresh interval has expired
- Issue HTTP HEAD requests (or equivalent) to check `Last-Modified` and `ETag` headers against cached metadata
- Mark documents as stale when the source has changed
- NOT re-fetch document content — only update the stale flag

#### Scenario: Document refresh interval expires
- **WHEN** a cached document's refresh interval has elapsed
- **THEN** document handler issues a HEAD request to the source URL
- **AND** compares response headers against cached metadata

#### Scenario: Source document unchanged
- **WHEN** HEAD request indicates content has not changed (matching Last-Modified/ETag)
- **THEN** document remains marked as fresh
- **AND** refresh timer resets

#### Scenario: Source document changed
- **WHEN** HEAD request indicates content has changed
- **THEN** document is marked as stale
- **AND** stale status is visible in listing tools

#### Scenario: HEAD request fails
- **WHEN** HEAD request fails (network error, timeout)
- **THEN** document retains its current stale/fresh status
- **AND** check is retried at next interval
