## MODIFIED Requirements

### Requirement: The system SHALL provide a `category_list_files` tool that lists all files in a category directory.

The tool SHALL merge filesystem files and stored documents in its output, with each entry indicating its source.

#### Scenario: List includes stored documents
- **WHEN** `category_list_files` is called for a category that has stored documents
- **THEN** output includes both filesystem files and stored documents
- **AND** each entry indicates whether it is from the filesystem or the document store

#### Scenario: List with no stored documents
- **WHEN** `category_list_files` is called for a category with no stored documents
- **THEN** behaviour is unchanged — only filesystem files are listed

## ADDED Requirements

### Requirement: Document Management Tools

The system SHALL provide MCP tools to manage documents in the external document store.

Tools:
- `document_add(category, name, source, source_type, content, metadata)` — add or update a document
- `document_remove(category, name)` — remove a document
- `document_update(category, name, content, metadata)` — update an existing document's content
- `document_list(category?)` — list documents, optionally filtered by category

#### Scenario: Add a document via tool
- **WHEN** `document_add` is called with valid parameters
- **THEN** the document is stored in the document store
- **AND** a success result is returned

#### Scenario: Remove a document via tool
- **WHEN** `document_remove` is called with an existing category and name
- **THEN** the document is removed from the store

#### Scenario: Remove a non-existent document
- **WHEN** `document_remove` is called with a non-existent key
- **THEN** an error result is returned

#### Scenario: List documents via tool
- **WHEN** `document_list` is called with a category filter
- **THEN** only documents in that category are returned

#### Scenario: List all documents via tool
- **WHEN** `document_list` is called without a category filter
- **THEN** all documents are returned
