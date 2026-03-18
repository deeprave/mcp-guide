## 1. Storage System
- [ ] 1.1 Add `get_documents_db()` path helper to `config_paths.py`
- [ ] 1.2 Create `src/mcp_guide/store/document_store.py` with SQLite schema and CRUD operations
- [ ] 1.3 Add tests for document store CRUD (add, get, update, remove, list by category)

## 2. Management MCP Tools
- [ ] 2.1 Create `document_add` tool (accepts category, name, source, content)
- [ ] 2.2 Create `document_remove` tool (by category + name)
- [ ] 2.3 Create `document_update` tool (update content/metadata for existing document)
- [ ] 2.4 Create `document_list` tool (list documents, filterable by category)
- [ ] 2.5 Register tools and add tests

## 3. Discovery
- [ ] 3.1 Refactor `discover_documents()` → `discover_document_files()` (filesystem, existing behaviour)
- [ ] 3.2 Add `discover_document_stored()` (query document store by category and patterns)
- [ ] 3.3 Create merged `discover_documents()` that combines both sources
- [ ] 3.4 Update `category_list_files` to include stored documents in output
- [ ] 3.5 Add tests for merged discovery

## 4. Content Integration
- [ ] 4.1 Update `get_category_content` to include stored documents matching category
- [ ] 4.2 Update `get_content` to include stored documents when resolving categories/collections
- [ ] 4.3 Update `export_content` to include stored documents
- [ ] 4.4 Add integration tests for content delivery with stored documents
