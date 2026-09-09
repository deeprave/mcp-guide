## ADDED Requirements

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
