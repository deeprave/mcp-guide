## ADDED Requirements

### Requirement: Document-ingestion authorisation
For HTTP(S) callers, a `send_file_content` request that includes the metadata
required to ingest a document into the SQLite store SHALL require the `user`
scope before the document task writes or updates a stored document. A file
content callback that does not request document ingestion SHALL retain its
existing access behaviour. Stdio callers SHALL retain unrestricted document
ingestion.

#### Scenario: User adds a document to the store
- **WHEN** a `user`-scoped HTTP(S) caller sends file content with valid
  document-ingestion metadata
- **THEN** the system SHALL apply the existing category validation and document
  upsert behaviour
- **AND** it SHALL persist the resulting document in the SQLite store

#### Scenario: Unauthenticated caller attempts document ingestion
- **WHEN** an unauthenticated HTTP(S) caller sends file content with
  document-ingestion metadata
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL not create or update a document-store row

#### Scenario: Stdio caller adds a document
- **WHEN** a stdio caller sends file content with valid document-ingestion
  metadata
- **THEN** the system SHALL apply the existing document-ingestion behaviour
- **AND** it SHALL not require a caller identity or scope
