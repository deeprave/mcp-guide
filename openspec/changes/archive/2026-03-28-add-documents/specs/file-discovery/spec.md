## MODIFIED Requirements

### Requirement: Document Discovery Function

The system SHALL provide a `discover_documents()` function that discovers files from both the filesystem and the document store, merged into a unified result.

The function SHALL be composed of two sub-functions:
- `discover_document_files(base_dir, patterns)` — filesystem discovery (existing behaviour)
- `discover_document_stored(category, patterns)` — query document store by category, filtered by patterns

The merged function applies category and pattern filtering uniformly to both sources.

#### Scenario: Discover filesystem files
- **WHEN** `discover_document_files(base_dir, patterns)` is called
- **THEN** files matching patterns in the directory are returned with FileInfo metadata

#### Scenario: Discover stored documents
- **WHEN** `discover_document_stored(category, patterns)` is called
- **THEN** documents matching the category and patterns are returned from the store

#### Scenario: Merged discovery
- **WHEN** `discover_documents()` is called with both filesystem and store context
- **THEN** results from both sources are combined
- **AND** each result indicates its source (filesystem or store)
