## ADDED Requirements

### Requirement: Document Update Tool

The MCP server SHALL provide a `document_update` tool that mutates stored documents in-place.

The tool SHALL require `category` and `name` parameters identifying the existing document.

The tool SHALL require at least one mutation parameter to be provided.

#### Scenario: Rename document
- **WHEN** agent calls `document_update` with category="docs", name="old.md", new_name="new.md"
- **THEN** the document is renamed and the updated record is returned

#### Scenario: Move document to different category
- **WHEN** agent calls `document_update` with category="docs", name="file.md", new_category="guides"
- **AND** category "guides" exists
- **THEN** the document is moved and the updated record is returned

#### Scenario: Rename and move simultaneously
- **WHEN** agent calls `document_update` with category="docs", name="old.md", new_name="new.md", new_category="guides"
- **THEN** both category and name are updated atomically

#### Scenario: Collision on rename/move
- **WHEN** agent calls `document_update` with a target (category, name) that already exists
- **THEN** tool returns an error indicating the target already exists

#### Scenario: Document not found
- **WHEN** agent calls `document_update` with a (category, name) that does not exist
- **THEN** tool returns a not-found error

#### Scenario: No mutation parameters
- **WHEN** agent calls `document_update` with only category and name
- **THEN** tool returns a validation error

### Requirement: Document Metadata Mutation

The `document_update` tool SHALL support three mutually exclusive metadata operations: add, replace, and clear.

Specifying more than one metadata operation SHALL be a validation error.

#### Scenario: Add metadata entries
- **WHEN** agent calls `document_update` with metadata_add={"author": "alice"}
- **THEN** the entries are merged into existing metadata

#### Scenario: Replace metadata
- **WHEN** agent calls `document_update` with metadata_replace={"type": "user/information"}
- **THEN** the entire metadata dict is replaced

#### Scenario: Clear metadata keys
- **WHEN** agent calls `document_update` with metadata_clear=["draft", "temp"]
- **THEN** the specified keys are removed from metadata

#### Scenario: Multiple metadata operations rejected
- **WHEN** agent calls `document_update` with both metadata_add and metadata_clear
- **THEN** tool returns a validation error indicating metadata operations are mutually exclusive

### Requirement: Store Description in Listings

The `category_list_files` tool SHALL surface descriptions for store-sourced documents by reading from the document record's metadata.

#### Scenario: Stored document with description
- **WHEN** a stored document has metadata containing "description"
- **THEN** `category_list_files` includes the description in the file listing

#### Scenario: Stored document without description
- **WHEN** a stored document has no "description" in metadata
- **THEN** `category_list_files` omits the description field for that entry

### Requirement: Document Show Command

The server SHALL provide a `document/show` command that displays full detail for a stored document.

The output SHALL include category, name, source, source_type, metadata, created_at, updated_at, and content size.

#### Scenario: Show existing document
- **WHEN** agent executes `document/show` with category and name
- **THEN** command returns all document fields and metadata

#### Scenario: Show non-existent document
- **WHEN** agent executes `document/show` with a (category, name) that does not exist
- **THEN** command returns a not-found error

### Requirement: Document Update Command

The server SHALL provide a `document/update` command template that renders output for all mutation combinations.

The template SHALL handle rename, move, and metadata operation results.

#### Scenario: Update command output
- **WHEN** a document is successfully updated via `document_update`
- **THEN** the `document/update` command template renders the mutation summary
