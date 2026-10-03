## ADDED Requirements

### Requirement: Document-ingestion authorisation
When provider-backed policy is active for a remote caller, a
`send_file_content` request that includes the metadata required to ingest a
document into the SQLite store SHALL require `user` access
before the document task writes or updates a stored document. A file-content
callback that does not request document ingestion SHALL retain its existing
access behaviour. When no provider is selected, remote callers SHALL retain
existing behaviour. Stdio callers SHALL retain unrestricted document ingestion.

#### Scenario: Caller adds a document to the store
- **WHEN** a user-scoped caller sends file content with valid document-ingestion
  metadata
- **THEN** the system SHALL apply the existing category validation and document
  upsert behaviour
- **AND** it SHALL persist the resulting document in the SQLite store

#### Scenario: Unauthenticated caller attempts document ingestion
- **WHEN** an unauthenticated caller sends document-ingestion metadata
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL not create or update a document-store row

#### Scenario: Ordinary file callback is unprotected
- **WHEN** a caller sends file content without document-ingestion metadata
- **THEN** it SHALL retain existing callback access behaviour

### Requirement: Document update and removal authorisation
When provider-backed policy is active for a remote caller, `document_update`
and `document_remove` SHALL require `user` access. Stdio SHALL retain existing
unrestricted behaviour.

#### Scenario: User updates or removes a document
- **WHEN** a user-scoped caller invokes `document_update` or `document_remove`
- **THEN** the system SHALL apply the existing document-store behaviour

#### Scenario: Unauthenticated caller mutates a document
- **WHEN** an unauthenticated caller invokes `document_update` or `document_remove`
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL not change the document-store row
