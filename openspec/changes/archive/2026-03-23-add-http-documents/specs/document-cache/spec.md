# Document Cache Specification

## ADDED Requirements

### Requirement: Persistent Document Cache
The system SHALL maintain a persistent document cache in a single-file compact format (SQLite) in the XDG cache directory.

Each cache entry SHALL store:
- Source URL
- Assigned pattern name
- Category and project association
- Markdown content
- Fetch timestamp
- Refresh interval
- Stale flag
- HTTP metadata (Last-Modified, ETag) for staleness checking

#### Scenario: Cache document after successful fetch
- **WHEN** agent sends converted markdown content via `send_file_content`
- **THEN** content is stored in persistent cache with full metadata
- **AND** stale flag is set to false

#### Scenario: Cache persists across sessions
- **WHEN** MCP session restarts
- **THEN** previously cached documents are available immediately
- **AND** no re-fetch is required for fresh documents

### Requirement: Cache Retrieval
The system SHALL retrieve cached documents by category and pattern for inclusion in content delivery.

#### Scenario: Retrieve cached document
- **WHEN** content delivery requests a URL-backed pattern
- **THEN** cached markdown content is returned
- **AND** retrieval is fast (indexed lookup)

#### Scenario: Missing cache entry
- **WHEN** a URL-backed pattern has no cache entry
- **THEN** system instructs agent to fetch and cache the document

### Requirement: Cache Eviction
The system SHALL evict cache entries when the corresponding URL/pattern is removed from a category.

#### Scenario: URL pattern removed from category
- **WHEN** a URL/pattern is removed via `category_update` or `category_change`
- **THEN** the corresponding cache entry MAY be evicted

### Requirement: Document Refresh Tool
The system SHALL provide a tool for the agent to refresh stale documents.

The refresh tool SHALL:
- List documents that are marked stale
- Accept re-fetched content from the agent to update the cache
- Clear the stale flag after successful refresh

#### Scenario: List stale documents
- **WHEN** refresh tool is called without arguments
- **THEN** system returns list of stale documents with source URLs

#### Scenario: Refresh stale document
- **WHEN** agent re-fetches a stale URL and submits updated markdown
- **THEN** cache entry is updated with new content and timestamp
- **AND** stale flag is cleared

### Requirement: send_file_content Document Format
The system SHALL define a specific file format for `send_file_content` that the document handler task can intercept and route to the cache.

#### Scenario: Agent submits fetched URL content
- **WHEN** agent calls `send_file_content` with the document cache format
- **THEN** document handler task intercepts the submission
- **AND** content is stored in the persistent cache
