## 1. Config path helper

- [x] 1.1 Add `get_documents_db()` to `config_paths.py` — returns `<config_dir>/documents.db`

## 2. Document store module

- [x] 2.1 Create `src/mcp_guide/store/__init__.py`
- [x] 2.2 Create `src/mcp_guide/store/document_store.py`:
  - `DocumentRecord` dataclass (all schema fields)
  - `_get_conn(db_path)` — open connection, create table + indexes if not exists
  - `add_document(category, name, source, source_type, content, metadata, db_path)` — upsert
  - `get_document(category, name, db_path)` → `DocumentRecord | None`
  - `remove_document(category, name, db_path)` → `bool` (True if row deleted)
  - `list_documents(category=None, db_path)` → `list[DocumentRecord]`

## 3. Tests

- [x] 3.1 Create `tests/unit/test_mcp_guide/store/test_document_store.py`:
  - add → get round-trip
  - upsert updates content and `updated_at`
  - get missing key returns `None`
  - remove existing row
  - remove missing key returns `False`
  - list by category
  - list all (no filter)
  - metadata stored and retrieved
