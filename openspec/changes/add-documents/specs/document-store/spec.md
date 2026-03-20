## ADDED Requirements

### Requirement: Document Store Schema

The system SHALL maintain a persistent SQLite database (`documents.db`) in the config directory with a single `documents` table.

Schema:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `category` TEXT NOT NULL — category assignment for the document
- `name` TEXT NOT NULL — unique key within category (typically the source document name)
- `source` TEXT NOT NULL — origin path (file path or URL)
- `source_type` TEXT NOT NULL — `'file'` or `'url'`
- `content` TEXT NOT NULL — markdown content
- `metadata` BLOB DEFAULT NULL — JSON-encoded source-specific fields (etag, last-modified, content-type, etc.)
- `created_at` TEXT NOT NULL — ISO 8601 timestamp
- `updated_at` TEXT NOT NULL — ISO 8601 timestamp
- UNIQUE constraint on (category, name)
- Indexes on `category` and `name`

#### Scenario: Database initialisation
- **WHEN** the document store is accessed for the first time
- **THEN** the database and table are created if they do not exist
- **AND** the database file is located in the config directory

#### Scenario: Schema supports upsert
- **WHEN** a document is added with a (category, name) that already exists
- **THEN** the existing row is updated with new content and metadata
- **AND** `updated_at` is set to the current timestamp

### Requirement: Document Store CRUD Operations

The system SHALL provide functions to add, get, update, remove, and list documents in the store.

#### Scenario: Add a document
- **WHEN** `add_document(category, name, source, source_type, content, metadata)` is called
- **THEN** a new row is inserted or existing row is updated
- **AND** timestamps are set appropriately

#### Scenario: Get a document
- **WHEN** `get_document(category, name)` is called with an existing key
- **THEN** the document row is returned with all fields

#### Scenario: Get a missing document
- **WHEN** `get_document(category, name)` is called with a non-existent key
- **THEN** None is returned

#### Scenario: Remove a document
- **WHEN** `remove_document(category, name)` is called
- **THEN** the matching row is deleted

#### Scenario: List documents by category
- **WHEN** `list_documents(category)` is called
- **THEN** all documents in that category are returned with metadata

#### Scenario: List all documents
- **WHEN** `list_documents()` is called without a category filter
- **THEN** all documents across all categories are returned

### Requirement: Document Store Path Helper

The system SHALL provide a `get_documents_db()` function in `config_paths.py` that returns the path to the SQLite database file.

#### Scenario: Database path resolution
- **WHEN** `get_documents_db()` is called
- **THEN** the path `<config_dir>/documents.db` is returned
