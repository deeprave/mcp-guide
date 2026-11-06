# document-store Specification

## Purpose
Define persistent storage, retrieval, and lifecycle management for user documents.

## Requirements

### Requirement: Document-store database location

The system SHALL maintain a persistent SQLite database named `documents.db` in
the config directory, with a single `documents` table.

#### Scenario: Database initialisation
- **WHEN** the document store is accessed for the first time
- **THEN** the database and table are created if they do not exist
- **AND** the database file is located in the config directory

### Requirement: Document-store identity schema

The `documents` table SHALL have an autoincrementing integer `id` primary key,
case-insensitive non-null `category` and `name` fields, a unique constraint on
`(category, name)`, and indexes on `category` and `name`.

#### Scenario: Unique document identity
- **WHEN** two documents use the same category and name
- **THEN** the store treats them as the same document identity

### Requirement: Document-store source and content schema

The `documents` table SHALL store a non-null `source` path or URL, a non-null
`source_type` of `file` or `url`, and non-null Markdown `content`.

#### Scenario: Source document storage
- **WHEN** a document is stored from a file or URL
- **THEN** its source, source type, and Markdown content are retained

### Requirement: Document-store metadata schema

The table SHALL store optional JSON-encoded metadata, including auto-detected
`content-type` and a frontmatter `type` of `agent/instruction` by default,
`agent/information`, or `user/information`.

#### Scenario: Document metadata storage
- **WHEN** a document is stored with content type and frontmatter type metadata
- **THEN** the metadata JSON retains those values

### Requirement: Document-store timestamp and source-mtime schema

The table SHALL store optional source `mtime` as an epoch float and non-null
ISO 8601 `created_at` and `updated_at` timestamps. Source mtime SHALL support
re-import staleness detection and remain distinct from store-write `updated_at`.

#### Scenario: Schema migration adds mtime column
- **WHEN** an existing database without the `mtime` column is opened
- **THEN** the `mtime` column is added via ALTER TABLE migration
- **AND** existing rows have `mtime` set to NULL

#### Scenario: Schema supports upsert
- **WHEN** a document is added with a (category, name) that already exists
- **THEN** the existing row is updated with new content, metadata, and mtime
- **AND** `updated_at` is set to the current timestamp

### Requirement: Bounded stored document content

The document store SHALL validate UTF-8 content byte length before committing an
add or replacement. It SHALL query stored byte size before materialising a
document body. In both cases an oversized body SHALL fail with
`max_size_exceeded`, preserving any existing replacement target.

#### Scenario: Oversized replacement preserves existing content
- **WHEN** a replacement exceeds the configured content limit
- **THEN** the operation fails before commit
- **AND** the previous body remains unchanged

### Requirement: Control-Safe Stored Document Names

The document store SHALL reject a document name containing any Unicode control
character, including CR, LF, NUL, DEL, and C1 controls. It SHALL apply this rule
to document addition, replacement/upsert, and rename operations before a database
write occurs. Names may otherwise retain existing nested path and Unicode support.

An unsafe name SHALL produce a validation failure and SHALL NOT create, replace,
rename, or otherwise modify a document row.

#### Scenario: Ingestion rejects CRLF document name
- **WHEN** document ingestion supplies a name containing CR or LF
- **THEN** the document is rejected as an invalid name
- **AND** no row containing that name is stored

#### Scenario: Rename rejects control character without altering row
- **WHEN** an existing stored document is renamed to a name containing NUL or another Unicode control character
- **THEN** the rename fails as invalid
- **AND** the document remains available under its original name and content

#### Scenario: Valid nested Unicode document name remains supported
- **WHEN** a caller adds or renames a document with a nested path and non-control Unicode characters
- **THEN** the operation succeeds under existing document-store semantics
- **AND** the stored name is preserved

### Requirement: Document-ingestion authorisation

When provider-backed policy is active for a remote caller, a
`send_file_content` request with the metadata required for document ingestion
SHALL require `user` access before the document task writes or updates a stored
document.

#### Scenario: Caller adds a document to the store
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** a user-scoped caller sends file content with valid document-ingestion
  metadata
- **THEN** the system SHALL apply the existing category validation and document
  upsert behaviour
- **AND** it SHALL persist the resulting document in the SQLite store

#### Scenario: Unauthenticated caller attempts document ingestion
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** an unauthenticated caller sends document-ingestion metadata
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL not create or update a document-store row

### Requirement: Non-ingestion file callback authorisation

A file-content callback that does not request document ingestion SHALL retain
its existing access behaviour.

#### Scenario: Ordinary file callback is unprotected
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** a caller sends file content without document-ingestion metadata
- **THEN** it SHALL retain existing callback access behaviour

### Requirement: Unrestricted document ingestion without provider policy

When no provider is selected, remote callers SHALL retain existing document
ingestion behaviour. Stdio callers SHALL retain unrestricted document ingestion.

#### Scenario: Stdio document ingestion
- **WHEN** a stdio caller sends valid document-ingestion metadata
- **THEN** the document task permits ingestion without provider-backed access checks

### Requirement: Document update and removal authorisation
When provider-backed policy is active for a remote caller, `document_update`
and `document_remove` SHALL require `user` access. Stdio SHALL retain existing
unrestricted behaviour.

#### Scenario: User updates or removes a document
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** a user-scoped caller invokes `document_update` or `document_remove`
- **THEN** the system SHALL apply the existing document-store behaviour

#### Scenario: Unauthenticated caller mutates a document
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** an unauthenticated caller invokes `document_update` or `document_remove`
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL not change the document-store row
