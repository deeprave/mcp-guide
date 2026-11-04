# Spec Delta

## MODIFIED Requirements

### Requirement: Document Discovery Function

The system SHALL provide a `discover_documents()` function that discovers files from both the filesystem and the document store, merged into a unified result.

The function SHALL be composed of two sub-functions:
- `discover_document_files(base_dir, patterns)` — filesystem discovery (existing behaviour)
- `discover_document_stored(category, patterns)` — query document store by category, filtered by patterns

The merged function applies category and pattern filtering uniformly to both sources.

A base directory that does not exist, or is not a directory, SHALL NOT be an error. Filesystem discovery SHALL skip the search and return an empty result, and the store SHALL still be consulted.

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

#### Scenario: Missing base directory
- **WHEN** `discover_document_files(base_dir, patterns)` is called and `base_dir` does not exist
- **THEN** an empty result is returned
- **AND** no exception is raised

#### Scenario: Base path is not a directory
- **WHEN** `discover_document_files(base_dir, patterns)` is called and `base_dir` is an existing file
- **THEN** an empty result is returned
- **AND** no exception is raised

#### Scenario: Store-only category in merged discovery
- **WHEN** `discover_documents()` is called for a category whose directory does not exist but which has matching stored documents
- **THEN** the stored documents are returned
- **AND** no exception is raised

#### Scenario: Nothing in either source
- **WHEN** `discover_documents()` is called for a category with no directory and no stored documents
- **THEN** an empty result is returned
