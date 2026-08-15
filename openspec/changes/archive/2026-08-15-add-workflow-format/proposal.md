## Why

The workflow state-file format is defined by an internal template, but the workflow monitor never renders it into a response. After an agent sends a workflow file with no semantic state changes, it receives only a cache acknowledgement, leaving the expected format unavailable through the workflow response path.

## What Changes

- Render the internal workflow state-format template after successfully parsing workflow file content when no semantic workflow-change response is produced.
- Return the rendered template through the originating `send_file_content` event so its `agent/instruction` disposition and embedded instruction are preserved without a shared response cache.
- Preserve the existing behavior when the template render returns `None`, which indicates workflow is disabled or the template is unavailable.
- Preserve semantic phase and field-change responses when workflow state changes are detected.
- Clarify that the workflow state-format template is strictly YAML, uses lowercase keys, permits omission of optional lines, and names the exact `send_file_content` MCP tool.
- Format the existing Markdown documents that Ruff reports as unformatted, without changing their prose or documented behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow-monitoring`: Return workflow state-format guidance with the file-content response when parsing succeeds but no semantic workflow-change response exists.
- `workflow-templates`: Define clear workflow state-file format guidance for optional fields, active changes, and `send_file_content`.

## Impact

- `src/mcp_guide/workflow/tasks.py`
- `src/mcp_guide/filesystem/tools.py` and task-manager event-response aggregation
- `src/mcp_guide/templates/_workflow/state-format.mustache`
- Workflow monitoring and filesystem response tests
- Workflow template rendering tests
- 34 archived OpenSpec/ADR and source README Markdown documents containing formatted Python examples
