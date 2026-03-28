## ADDED Requirements

### Requirement: Document Store Schema

The system SHALL maintain a persistent SQLite database (`documents.db`) in the config directory with a single `documents` table.

Schema:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `category` TEXT NOT NULL COLLATE NOCASE — category assignment for the document
- `name` TEXT NOT NULL COLLATE NOCASE — unique key within category (typically the source document name)
- `source` TEXT NOT NULL — origin path (file path or URL)
- `source_type` TEXT NOT NULL — `'file'` or `'url'`
- `content` TEXT NOT NULL — markdown content
- `metadata` BLOB DEFAULT NULL — JSON-encoded fields (content-type, type, etag, last-modified, etc.)
- `mtime` REAL DEFAULT NULL — source modification time as epoch float (like os.stat().st_mtime)
- `created_at` TEXT NOT NULL — ISO 8601 timestamp
- `updated_at` TEXT NOT NULL — ISO 8601 timestamp
- UNIQUE constraint on (category, name)
- Indexes on `category` and `name`

The `mtime` column records the source file's modification time, distinct from `updated_at` which tracks when the store was last written. It is used for staleness detection on re-import.

The `metadata` JSON blob SHALL store:
- `content-type` — auto-detected MIME type of the content
- `type` — frontmatter document type (`agent/instruction`, `agent/information`, `user/information`), defaulting to `agent/instruction`

#### Scenario: Database initialisation
- **WHEN** the document store is accessed for the first time
- **THEN** the database and table are created if they do not exist
- **AND** the database file is located in the config directory

#### Scenario: Schema migration adds mtime column
- **WHEN** an existing database without the `mtime` column is opened
- **THEN** the `mtime` column is added via ALTER TABLE migration
- **AND** existing rows have `mtime` set to NULL

#### Scenario: Schema supports upsert
- **WHEN** a document is added with a (category, name) that already exists
- **THEN** the existing row is updated with new content, metadata, and mtime
- **AND** `updated_at` is set to the current timestamp
