# Accept full path in set_project

**Status**: Implemented
**Priority**: High
**Complexity**: Medium

## Why

When an agent like Codex connects without MCP roots and without `$PWD`, the session stays unbound and nothing works. The agent needs a way to establish project context using the only thing it knows — its working directory path. Additionally, error responses were inconsistent, resource handlers bypassed the TaskManager pipeline, and session state was lost across async Tasks.

## What Changed

### Path handling in set_project
- `session.switch_project` accepts full paths and `file://` URIs
- Validates absolute path, no `..` traversals
- Extracts basename as project name, updates roots

### Consistent no-project enforcement
- Static `RESULT_NO_PROJECT` with emphatic instruction text
- `requires_project` parameter on `toolfunc` decorator — all tools except `set_project` require a bound project
- Replaces 30+ ad-hoc error returns across 7 tool files

### Resource handlers through TaskManager pipeline
- Resource handlers now go through `process_result` → `to_json_str()`
- `additional_agent_instructions` now surfaces on resource reads (was silently dropped)

### Session persistence across async Tasks
- `get_or_create_session` checks `_session_registry` when ContextVar is empty
- Fixes session loss between tool calls in Codex/stdio transport

### Instruction clarity
- Status template: conditional instruction based on workflow state
- Monitoring/tracking templates: emphatic `send_file_content` tool references

## Impact

- Codex can now connect and operate with mcp-guide end-to-end
- Any agent without roots/PWD can bind via `set_project`
- All agents get consistent, actionable error when project is unbound
