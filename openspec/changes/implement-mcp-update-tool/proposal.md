# Implement MCP Update Tool

**Status**: Proposed
**Priority**: High
**Complexity**: Medium

## Why

Users need a way to update documentation files when the mcp-guide package is updated. Currently, updates require manual reinstallation or running the `mcp-install` script. This change provides an MCP tool that agents can invoke to perform smart updates, plus optional automatic update prompting via feature flag.

## What Changes

- Add `update_documents` tool (no arguments) that updates docroot using same logic as `mcp-install update`
- Add global feature flag `autoupdate` (boolean) with validation to prevent project-level usage
- Add `McpUpdateTask` that checks flag once at startup and queues instruction if enabled
- Reuse existing installer logic (`update_templates` renamed to `update_docs`) with `lock_update()` for exclusive access
- Tool validates `.version` file and compares with current package version

## Impact

- Affected specs: `tool-infrastructure`, `task-manager`, `workflow-flags`, `installation`
- Affected code:
  - `src/mcp_guide/tools/` (new tool)
  - `src/mcp_guide/tasks/` (new task)
  - `src/mcp_guide/installer/core.py` (rename function, add safety check)
  - `src/mcp_guide/scripts/mcp_guide_install.py` (add safety check)
  - `src/mcp_guide/feature_flags/` (flag validation)
- New template: `_commands/update-prompt.mustache` (instruction for agent)
- **BREAKING**: Adds safety check to prevent docroot == template source (affects both tool and script)
