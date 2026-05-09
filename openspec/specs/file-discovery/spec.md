# file-discovery Specification

## Purpose
Define how project documents are discovered from configured filesystem
categories and the local document store, including pattern matching,
source identity, and deduplication behavior before content rendering.

## Requirements
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

### Requirement: Source-Aware Document Deduplication

The system SHALL deduplicate discovered documents using source-aware identity
rather than display basename.

Filesystem documents SHALL be identified by their source path identity. Stored
documents SHALL be identified by `(category, name)`. Filesystem and stored
documents SHALL remain distinct sources, even when their display names match.

#### Scenario: Files with same basename from different directories
- **WHEN** filesystem discovery matches multiple files with the same basename in
  different directories
- **THEN** all matching files SHALL be included
- **AND** no file SHALL be silently skipped because another file has the same
  basename

#### Scenario: Template and non-template variants of same source path
- **WHEN** filesystem discovery matches template and non-template variants of
  the same source path
- **THEN** the variants SHALL be deduplicated using the full relative path with
  template extension stripped
- **AND** the preferred variant SHALL be returned according to discovery rules

#### Scenario: Stored document overlaps multiple collections
- **WHEN** the same stored document is discovered through overlapping
  collections or expressions
- **THEN** the document SHALL appear once for its `(category, name)` identity

#### Scenario: Filesystem and stored document with same display name
- **WHEN** a filesystem document and a stored document have the same display name
- **THEN** both documents SHALL be returned
- **AND** they SHALL remain distinguishable by source
