# Change: Add Export Management Tools

## Why
The export story is incomplete. Users can export content via `export_content` but have no way to:
- List what has been exported
- See if exports are stale (source files changed)
- Remove export tracking entries

This creates a blind spot where exports accumulate without visibility or management.

## What Changes
- Add `list_exports` tool that returns raw JSON array of export entries with metadata
- Add `remove_export` tool that removes tracking entries from `Project.exports`
- Add `parse_options` utility for converting display option lists to template context dicts
- Reorganize export commands under `_commands/export/` directory:
  - Move existing export command to `export/add.mustache` with alias 'export'
  - Add `export/list.mustache` command for formatted display
  - Add `export/remove.mustache` command for removing tracking
- Add `_system/_exports-format.mustache` template for formatting export lists

`list_exports` accepts an `options` parameter (`list[str]`) that controls template rendering:
- Empty options: returns raw JSON
- Non-empty options: renders via display template with options merged into context
- Supports truthy flags (`"verbose"`) and key=value pairs (`"limit=10"`)
- See `openspec/adr/passing-template-arguments-to-tools.md` for design rationale

Export list includes:
- expression (content identifier)
- pattern (optional file pattern)
- path (export destination)
- exported_at (timestamp from file mtime)
- stale (boolean indicating if source files changed)

## Impact
- Affected specs: `content-tools`, `knowledge-export`, `help-template-system`
- Affected code: `src/mcp_guide/tools/tool_content.py`, `src/mcp_guide/tools/tool_result.py`, `src/mcp_guide/templates/`
- No breaking changes
