## 1. Storage System
- [x] 1.1 Add `get_documents_db()` path helper to `config_paths.py`
- [x] 1.2 Create `src/mcp_guide/store/document_store.py` with SQLite schema and CRUD operations
- [x] 1.3 Add tests for document store CRUD (add, get, update, remove, list by category)

## 2. Schema Update
- [ ] 2.1 Add `mtime REAL DEFAULT NULL` column via migration in `_MIGRATIONS`
- [ ] 2.2 Update `add_document` to accept and store `mtime`
- [ ] 2.3 Update `DocumentRecord` dataclass with `mtime` field
- [ ] 2.4 Add tests for mtime storage and migration

## 3. Document Ingestion Task
- [ ] 3.1 Create `DocumentTask` in task_manager that subscribes to `FS_FILE_CONTENT` events
- [ ] 3.2 Match events by presence of required metadata fields (category, source, mtime)
- [ ] 3.3 Validate category exists in project configuration
- [ ] 3.4 Default document name to basename of path if not provided
- [ ] 3.5 Auto-detect content-type using existing MIME handler functions
- [ ] 3.6 Implement mtime-based staleness: reject same mtime, update newer, force overwrite
- [ ] 3.7 Store `type` and `content-type` in metadata JSON blob
- [ ] 3.8 Add tests for ingestion, staleness, force, validation, and event passthrough

## 4. Document Remove Tool
- [ ] 4.1 Create `document_remove` MCP tool (category + name)
- [ ] 4.2 Add tests for remove existing and non-existent documents

## 5. Category List Files Update
- [ ] 5.1 Add optional `source` filter parameter to `category_list_files` (files, stored, default=both)
- [ ] 5.2 Include source indicator in each response entry
- [ ] 5.3 Add tests for source filtering

## 6. Discovery
- [x] 6.1 Refactor `discover_documents()` → `discover_document_files()` (filesystem, existing behaviour)
- [x] 6.2 Add `discover_document_stored()` (query document store by category and patterns)
- [x] 6.3 Create merged `discover_documents()` that combines both sources
- [ ] 6.4 Update `category_list_files` to use merged discovery with source filter
- [ ] 6.5 Add tests for merged discovery in category listing

## 7. Content Integration
- [ ] 7.1 Update `get_category_content` to include stored documents matching category
- [ ] 7.2 Update `get_content` to include stored documents when resolving categories/collections
- [ ] 7.3 Update `export_content` to include stored documents
- [ ] 7.4 Add integration tests for content delivery with stored documents
