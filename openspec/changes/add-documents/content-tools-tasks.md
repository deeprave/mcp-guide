# add-documents/content-tools Implementation Plan

Integrates stored documents into the content delivery pipeline and provides document management via task-based ingestion and a remove tool.

## Section 1: Schema Update

Add `mtime` column to document store for source modification time tracking.

- [x] 1.1 Add `ALTER TABLE documents ADD COLUMN mtime REAL DEFAULT NULL` to `_MIGRATIONS`
- [x] 1.2 Add `mtime: Optional[float] = None` field to `DocumentRecord`
- [x] 1.3 Update `add_document()` to accept and persist `mtime` parameter
- [x] 1.4 Update `_METADATA_FIELDS` / `_SELECT_METADATA` derivation (automatic from dataclass)
- [x] 1.5 Add tests: mtime stored on add, mtime returned on get/list, migration on existing DB

## Section 2: Document Ingestion Task

Create `DocumentTask` that listens for `FS_FILE_CONTENT` events and ingests documents into the store when required metadata fields are present.

- [x] 2.1 Create `src/mcp_guide/tasks/document_task.py` implementing `TaskSubscriber` protocol
- [x] 2.2 Subscribe to `EventType.FS_FILE_CONTENT`, match events containing `category` + `source` in data dict
- [x] 2.3 Default `name` to `Path(data["path"]).name` if not in data
- [x] 2.4 Validate category exists in project configuration
- [x] 2.5 Auto-detect content-type via `MimeFormatter._detect_text_subtype` (extract to module-level function or reuse)
- [x] 2.6 Store `content-type` and optional `type` (default `agent/instruction`) in metadata JSON
- [x] 2.7 Implement mtime staleness: same mtime → reject, newer mtime → update, force → always overwrite
- [x] 2.8 Register `DocumentTask` in task manager startup
- [x] 2.9 Add tests: new doc ingestion, mtime reject, mtime update, force overwrite, invalid category, missing metadata passthrough

## Section 3: Document Remove Tool

Single dedicated MCP tool for deleting stored documents.

- [x] 3.1 Add `document_remove` tool with `category` and `name` arguments
- [x] 3.2 Return error if document does not exist
- [x] 3.3 Add tests for successful removal and non-existent document

## Section 4: Category List Files Source Filter

Extend `category_list_files` to support filtering by source.

- [x] 4.1 Add optional `source` parameter to `CategoryListFilesArgs` (values: `files`, `stored`, default: both)
- [x] 4.2 Use `discover_documents()` when source includes stored, `discover_document_files()` for files-only
- [x] 4.3 Include `source` field (`file` or `store`) in each response entry
- [x] 4.4 Add tests for each filter value and mixed results

## Section 5: Content Integration

Update content tools to serve stored documents alongside filesystem files.

- [x] 5.1 Update `gather_content` / `get_category_content` to pass category name to `discover_documents()`
- [x] 5.2 Verify `get_content` works via collection → category → discover_documents chain
- [x] 5.3 Verify `export_content` includes stored documents (should follow from 5.1)
- [x] 5.4 Add integration tests for content delivery with stored documents

## Section 6: Frontmatter Handling in Document Ingestion

Parse and strip frontmatter from document content during ingestion, merging into metadata with correct precedence.

- [x] 6.1 Parse content with `parse_content_with_frontmatter()` in `DocumentTask.handle_event`
- [x] 6.2 Strip frontmatter from content before storage (use `parsed.content`)
- [x] 6.3 Merge metadata: `{**parsed.frontmatter, **event_metadata, "content-type": ..., "type": ...}`
- [x] 6.4 Run `detect_text_subtype` on stripped content (not raw)
- [x] 6.5 Add tests: content with frontmatter stripped, frontmatter merged into metadata, event metadata overrides frontmatter, content without frontmatter unchanged

## Section 7: Fix Cross-Source Dedup in Content Gathering

The dedup in `gather_content` uses a single `absolute_path` key for all files. Filesystem files and stored documents have different natural keys and must be deduped separately:
- Filesystem files: dedup by absolute path (unchanged)
- Stored documents: dedup by `(category_name, document_name)` — their natural uniqueness key

- [x] 7.1 Separate dedup: filesystem files by `absolute_path`, stored documents by `(category, name)`
- [x] 7.2 Add test: stored and filesystem file with same name both appear in output
- [x] 7.3 Add test: same stored document via overlapping collections is deduped

## Section 8: Wire send_file_content for Document Ingestion

Add optional document ingestion fields to `SendFileContentArgs` and forward through the `FS_FILE_CONTENT` event payload so agents can trigger `DocumentTask` via the existing tool.

- [x] 8.1 Add optional `category`, `source`, `name`, `type`, `force` fields to `SendFileContentArgs`
- [x] 8.2 Add matching parameters to `send_file_content()` in `filesystem/tools.py`
- [x] 8.3 Forward non-None fields into the event data dict
- [x] 8.4 Add test: event data includes ingestion fields when provided

## Section 9: Type Validation in DocumentTask

Guard against agent-provided non-string/non-numeric values in event data.

- [x] 9.1 Validate `category` and `source` are strings, return error if not
- [x] 9.2 Validate `mtime` is numeric (guard against bool subclass of int), coerce int to float
- [x] 9.3 Add tests: non-string category, non-string source, non-numeric mtime, int mtime coerced to float
