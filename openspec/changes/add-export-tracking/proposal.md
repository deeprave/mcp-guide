# Change: Track export_content operations to avoid redundant exports

## Why

Agents repeatedly export the same content to their knowledge bases, consuming context window and tokens unnecessarily. When content hasn't changed since last export, the agent should be informed the content is already available rather than re-exporting it.

## What Changes

- Add per-project export tracking (expression, path, timestamp)
- Modify `export_content` to check if content unchanged since last export
- Return "already exported" message when content is current
- Add `force` flag to override staleness check
- Filter file discovery by export timestamp to detect changes efficiently

## Impact

- Affected specs: `content-tools`
- Affected code: `tool_content.py`, `project_config.py`, `models.py`, `discovery.py`
- Non-breaking: existing `export_content` calls work unchanged
- Performance: reduces redundant exports and context consumption
