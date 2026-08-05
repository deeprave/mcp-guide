## Why

The workflow state-file format is defined by an internal template, but the workflow monitor never renders it into a response. After an agent sends a workflow file with no semantic state changes, it receives only a cache acknowledgement, leaving the expected format unavailable through the workflow response path.

## What Changes

- Render the internal workflow state-format template after successfully parsing workflow file content when no semantic workflow-change response is produced.
- Use the rendered template as the `send_file_content` response so its `agent/instruction` disposition and embedded instruction are preserved.
- Preserve the existing behavior when the template render returns `None`, which indicates workflow is disabled or the template is unavailable.
- Preserve semantic phase and field-change responses when workflow state changes are detected.
- Clarify the workflow state-format template's required and optional fields, MCP tool usage, and concise file-update instructions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow-monitoring`: Return workflow state-format guidance with the file-content response when parsing succeeds but no semantic workflow-change response exists.
- `workflow-templates`: Define clear workflow state-file format guidance for optional fields, active changes, and `send_file_content`.

## Impact

- `src/mcp_guide/workflow/tasks.py`
- `src/mcp_guide/filesystem/tools.py` response aggregation behavior as exercised through the workflow task
- `src/mcp_guide/templates/_workflow/state-format.mustache`
- Workflow monitoring and filesystem response tests
- Workflow template rendering tests
