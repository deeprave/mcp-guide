# Change: Track export_content operations to avoid redundant exports

## Why

Agents repeatedly export the same content to their knowledge bases, consuming context window and tokens unnecessarily. When content hasn't changed since last export, the agent should be informed the content is already available rather than re-exporting it.

## What Changes

- Add per-project export tracking (expression, path, timestamp)
- Modify `export_content` to check if content unchanged since last export
- Return "already exported" message when content is current
- Add `force` flag to override staleness check
- Filter file discovery by export timestamp to detect changes efficiently
- Rename `discover_category_files()` → `discover_documents()` for clarity (function is used for commands, categories, and generic file discovery)

## Impact

- Affected specs: `content-tools`, `file-discovery`
- Affected code: `tool_content.py`, `project_config.py`, `models.py`, `discovery/files.py` (rename + signature change)
- Non-breaking: existing `export_content` calls work unchanged
- API change: `discover_category_files()` renamed to `discover_documents()` (internal API, 28 call sites updated)
- Performance: reduces redundant exports and context consumption
