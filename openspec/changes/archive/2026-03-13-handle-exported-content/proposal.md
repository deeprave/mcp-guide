# Change: Handle Exported Content with Knowledge Base Integration

## Why

When content is exported to external files for knowledge indexing, we're duplicating context unnecessarily. Agents with semantic indexing capabilities (like kiro/q-dev's knowledge tool) should be instructed to use their indexed knowledge rather than re-reading the full content. This reduces token usage and improves efficiency.

Additionally, the current hardcoded instruction in `export_content` is inflexible and doesn't accommodate different agent capabilities or scenarios.

## What Changes

- Create new `_system` template category for non-feature-specific system templates
- Move `_startup.mustache` and `_update.mustache` to `_system/` directory
- Create `_system/export.mustache` template for export instructions
- Add optional `force` boolean argument to `get_content` tool
- Refactor `export_content` to render instructions via template instead of hardcoding
- Modify `get_content` to check for exported content and return reference instructions unless forced
- Template will conditionally provide instructions based on:
  - Whether content is new or being overwritten
  - Whether content has been updated since last export
  - Agent capabilities (knowledge indexing support)
  - File path for direct access when knowledge indexing unavailable

## Impact

- Affected specs: `content-tools`, `template-system`
- Affected code:
  - `src/mcp_guide/tools/tool_content.py` (export_content function)
  - `src/mcp_guide/templates/` (new `_system/` directory)
  - Template discovery/rendering infrastructure
- Breaking: None (internal refactoring only)
