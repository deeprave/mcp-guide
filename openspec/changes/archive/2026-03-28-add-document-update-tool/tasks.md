## 1. Store layer — `_update_document()` in `document_store.py`

- [x] 1.1 Add `_update_document()` and async `update_document()` wrapper
- [x] 1.2 Validate metadata operations are mutually exclusive
- [x] 1.3 Check target (new_category, new_name) for collisions before update
- [x] 1.4 Add unit tests: rename, move, rename+move, metadata_add, metadata_replace, metadata_clear, collision, not found, no mutation, multiple metadata ops

## 2. Tool layer — `tool_document_update.py`

- [x] 2.1 Create `DocumentUpdateArgs` and `document_update` tool with `@toolfunc`
- [x] 2.2 Validate target category exists (if new_category specified)
- [x] 2.3 Register in `tools/__init__.py`
- [x] 2.4 Add integration tests: rename, move validates category, not found, collision, metadata_add, mutual exclusivity

## 3. Enrich `category_list_files` for stored docs

- [x] 3.1 Add optional `name` filter to `CategoryListFilesArgs`
- [x] 3.2 Enrich stored doc output with metadata dict, source_type, source_path, created_at, updated_at, description
- [x] 3.3 Add tests for name filter and enriched stored doc info

## 4. Command templates

- [x] 4.1 Create `_commands/document/show.mustache` — uses `category_list_files` with source=stored and name filter
- [x] 4.2 Create `_commands/document/update.mustache` — calls `document_update` with all optional kwargs

## 5. Check

- [x] 5.1 1674 tests passed, ruff check clean, ruff format clean, ty check clean
