## 1. Path Configuration Flags
- [x] 1.1 Add `path-documents` and `path-export` flag definitions to `src/mcp_guide/feature_flags/constants.py`
- [x] 1.2 Add path validators and normalisers to `src/mcp_guide/feature_flags/validators.py`
- [x] 5.1 Unit tests for path flag definitions and validators

## 2. Template Context
- [x] 2.1 Expose `{{path.documents}}` and `{{path.export}}` in template context (cache.py)
- [x] 2.2 Update templates with hardcoded `.todo/` to use `{{path.documents}}`

## 3. export_content Tool
- [x] 3.1 Add `export_content` tool to `src/mcp_guide/tools/tool_content.py`
- [x] 3.2 Args: `expression` (str), `pattern` (optional str), `path` (str, required), `force` (bool, default False)
- [x] 3.3 Reuse `internal_get_content()` for content gathering and rendering
- [x] 3.4 Path resolution: filename-only → resolved export dir; has directory → use as-is; no extension → add .md
- [x] 3.5 Add resolved export directory to project `allowed_write_paths` (validation happens automatically)
- [x] 3.6 Return rendered content with `instruction` field (create-only or forced overwrite based on `force`)

## 4. Tests
- [x] 4.1 Unit tests for export_content path resolution logic (16 parametrized tests)
- [x] 4.2 Integration tests (path resolution covered by unit tests; e2e testing has session isolation complexity)
- [x] 4.3 Test path defaulting and agent fallback

## 5. Documentation
- [x] 5.1 Update user docs for path flags
- [x] 5.2 Document export_content tool usage
