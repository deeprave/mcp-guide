# Change: External Document Store

## Why

Categories currently only reference local server-side files in docroot. Projects need the ability to include content from external sources — client-side files uploaded by the agent, or markdown fetched from HTTP URLs. Both share the same lifecycle (ingest → store → serve) and should use a unified storage mechanism.

This supersedes `add-client-documents` and `add-http-documents`.

## What Changes

- Add a persistent SQLite document store in the config directory (`documents.db`)
- Single flat table indexed on category and name, storing markdown content with source metadata
- Source-agnostic: documents may originate from local files or HTTP URLs
- Project-independent — documents are available to all projects, like docroot files
- MCP tools to add, remove, update, and list stored documents
- Refactor `discover_documents()` into filesystem and stored variants, merged for content delivery
- Content tools (`get_content`, `get_category_content`, `export_content`) serve stored documents alongside filesystem files
- `category_list_files` merges filesystem and stored document listings

## Impact

- Affected specs: `document-store` (ADDED), `file-discovery` (MODIFIED), `content-tools` (MODIFIED), `category-tools` (MODIFIED)
- Affected code:
  - New `src/mcp_guide/store/` module (SQLite document store)
  - `src/mcp_guide/tools/tool_content.py` (serve stored documents)
  - `src/mcp_guide/tools/tool_category.py` (list stored documents)
  - `src/mcp_guide/content/discover.py` (refactored discovery)
  - `src/mcp_guide/config_paths.py` (DB path helper)
