## MODIFIED Requirements

### Requirement: category_list_files Tool

The system SHALL provide a `category_list_files` tool that lists all files in a category directory.

The tool SHALL accept an optional `source` filter parameter to control which entries are returned:
- `files` — filesystem files only (current behaviour)
- `stored` — stored documents only
- No filter (default) — both filesystem files and stored documents

Each entry in the response SHALL indicate its source (`file` or `store`).

#### Scenario: List all sources (default)
- **WHEN** `category_list_files` is called without a source filter
- **THEN** output includes both filesystem files and stored documents
- **AND** each entry indicates its source

#### Scenario: List filesystem files only
- **WHEN** `category_list_files` is called with source filter `files`
- **THEN** only filesystem files are returned

#### Scenario: List stored documents only
- **WHEN** `category_list_files` is called with source filter `stored`
- **THEN** only stored documents are returned

#### Scenario: No stored documents exist
- **WHEN** `category_list_files` is called for a category with no stored documents
- **THEN** behaviour is unchanged — only filesystem files are listed

## ADDED Requirements

### Requirement: Document Remove Tool

The system SHALL provide a `document_remove` MCP tool to delete a document from the store by category and name.

#### Scenario: Remove an existing document
- **WHEN** `document_remove` is called with a valid category and name
- **THEN** the document is removed from the store
- **AND** a success result is returned

#### Scenario: Remove a non-existent document
- **WHEN** `document_remove` is called with a non-existent category/name
- **THEN** an error result is returned

### Requirement: Document Ingestion via Task Manager

The system SHALL provide a `DocumentTask` registered with the task manager that listens for `FS_FILE_CONTENT` events and ingests documents into the store.

The task SHALL match events based on the presence of required metadata fields, not path patterns. Other tasks listening for `FS_FILE_CONTENT` continue to receive the event independently.

Required fields in event data:
- `category` — must reference an existing category (validated)
- `name` — document name as stored; defaults to basename of the path if not provided
- `source` — origin identifier (file path or URL)
- `mtime` — source modification time (epoch float)
- `content` — document body

Optional fields:
- `force` — overwrite regardless of mtime (default false)
- `type` — frontmatter type: `agent/instruction` (default), `agent/information`, `user/information`

Content-Type SHALL be auto-detected from the content using the public `detect_text_subtype` function from `mcp_guide.content.formatters.mime` and stored in the metadata JSON blob. This function MUST NOT be accessed as a private method.

#### Scenario: Ingest a new document
- **WHEN** a `FS_FILE_CONTENT` event contains the required metadata fields
- **AND** no document with that category/name exists
- **THEN** the document is added to the store with auto-detected content-type
- **AND** the event result confirms successful ingestion

#### Scenario: Update with newer mtime
- **WHEN** a `FS_FILE_CONTENT` event matches an existing document
- **AND** the event mtime is newer than the stored mtime
- **THEN** the document content, metadata, and mtime are updated

#### Scenario: Reject update with same mtime
- **WHEN** a `FS_FILE_CONTENT` event matches an existing document
- **AND** the event mtime equals the stored mtime
- **AND** force is not set
- **THEN** the event result returns an error indicating no change

#### Scenario: Force overwrite
- **WHEN** a `FS_FILE_CONTENT` event contains force=true
- **THEN** the document is updated regardless of mtime comparison

#### Scenario: Invalid category
- **WHEN** a `FS_FILE_CONTENT` event references a non-existent category
- **THEN** the event result returns a validation error

#### Scenario: Event without required metadata
- **WHEN** a `FS_FILE_CONTENT` event lacks the required metadata fields
- **THEN** the DocumentTask does not match and the event passes through to other listeners
