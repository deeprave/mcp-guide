## 1. Control-safe document persistence

- [x] 1.1 Add a shared document-name validator that rejects all Unicode control code points while preserving nested paths and ordinary Unicode names, and verify focused unit parametrisation covers CR, LF, NUL, DEL, C1 controls, and valid names.
- [x] 1.2 Apply validation before SQLite add/upsert and rename mutations, and verify store tests prove invalid additions create no row and invalid renames leave the original row and content unchanged.
- [x] 1.3 Validate event-derived document names before document ingestion persists data, and verify DocumentTask tests return a stable invalid-name result without storing an unsafe event name.

## 2. Safe MIME content locations

- [x] 2.1 Add a shared UTF-8 URI path-segment encoder for MIME content locations after existing suffix and content-type extension handling, and verify safe ASCII paths retain their current locations.
- [x] 2.2 Use the shared location encoder in both single-document and multipart MIME formatting, and verify tests cover spaces, percent signs, reserved characters, Unicode, and nested path separators.
- [x] 2.3 Add a legacy-row regression fixture containing control characters and verify parsed MIME output has no injected headers or parser defects while the location uses percent encoding.

## 3. Verification

- [x] 3.1 Run `uv run pytest tests/unit/test_mcp_guide/store/test_document_store.py tests/unit/test_mcp_guide/tasks/test_document_task.py tests/unit/test_mcp_guide/content/formatters/test_mime.py` in the foreground and verify all affected unit tests pass.
- [x] 3.2 Run document metadata/discovery integration coverage in the foreground and verify valid stored documents still round-trip through MIME content formatting.
- [x] 3.3 Validate the completed OpenSpec change with `openspec validate fix-document-storage --type change --strict` and verify no validation errors remain.
