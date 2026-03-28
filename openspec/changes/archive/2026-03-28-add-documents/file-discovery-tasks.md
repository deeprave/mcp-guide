## 1. Document store refactor (adjust for lazy content loading)

- [x] 1.1 Make `DocumentRecord.content` optional (`Optional[str] = None`)
- [x] 1.2 Add `_get_document_content(category, name)` → `Optional[str]` (SELECT content only)
- [x] 1.3 Change `_get_document` and `_list_documents` to exclude `content` from SELECT
- [x] 1.4 Add async `get_document_content()` wrapper
- [x] 1.5 Update existing store tests for content-less records and new content function

## 2. FileInfo content_loader support

- [x] 2.1 Add `content_loader: Optional[Callable[[], Awaitable[Optional[str]]]]` parameter to `FileInfo.__init__`
- [x] 2.2 Update `_load_content_if_needed()` to use `content_loader` when provided (before filesystem fallback)
- [x] 2.3 Add `source: str = "file"` attribute to `FileInfo`
- [x] 2.4 Add tests for FileInfo with content_loader

## 3. Discovery refactor

- [x] 3.1 Rename `discover_documents()` → `discover_document_files()` (filesystem only)
- [x] 3.2 Update all call sites to use `discover_document_files()`
- [x] 3.3 Add `discover_document_stored(category, patterns)` — queries store, returns `FileInfo` list with content_loader and `source="store"`
- [x] 3.4 Add merged `discover_documents(base_dir, patterns, category)` combining both sources
- [x] 3.5 Update existing discovery tests for rename, add tests for stored and merged discovery
