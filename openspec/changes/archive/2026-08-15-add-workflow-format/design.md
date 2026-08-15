## Context

`WorkflowMonitorTask` parses received workflow-file content and returns an `EventResult` to the originating filesystem event. The internal `_workflow/state-format.mustache` template defines the format but is neither directly exposed through Guide nor rendered by the monitor.

`RenderedContent` retains the template's frontmatter-derived instruction and type. Event-result aggregation copies content and instruction into `Result`, but not its `disposition` field.

## Goals / Non-Goals

**Goals:**

- Return rendered workflow-format guidance in response to successfully parsed workflow-file content when no semantic-change response is available.
- Preserve the template's content, instruction, and `agent/instruction` disposition in the response.
- Leave disabled workflow behavior unchanged when `state-format` is filtered and renders as `None`.
- Preserve existing semantic workflow-change responses.
- Make the state-format template accurately document optional fields and the `send_file_content` MCP tool.
- Apply the configured formatter to the existing unformatted Markdown documentation without changing documentation meaning.

**Non-Goals:**

- Expose `_workflow/state-format.mustache` through a `guide://` URI.
- Change bootstrap or timer-driven queued instructions.
- Change the workflow state-file schema.
- Revise documentation prose or technical decisions as part of formatter-only cleanup.

## Decisions

### Return rendered content with the originating event

When parsing succeeds and no semantic change response was rendered, `WorkflowMonitorTask` will render `state-format`. A non-`None` result will be attached to its `EventResult`, causing the originating `send_file_content` response to contain rendered guidance.

This binds the response to the originating request. The existing event aggregation path already carries rendered content for other tasks; it will preserve the rendered content disposition as well.

### Preserve template disposition during aggregation

Event-result aggregation will copy the selected rendered content's `template_type` into `Result.disposition` together with its content and instruction. This makes the response's agent-facing disposition match `state-format` frontmatter and correctly represents all aggregated rendered responses as `agent/instruction`.

### Render only as fallback

The state-format template is fallback guidance, not an addition to a semantic-change response. A detected state change continues to use its existing phase or monitoring response. A `None` format render produces no override, so the existing cache acknowledgement remains for workflow-disabled projects.

### Keep field conditions in prose below the YAML example

The YAML block will remain a compact structural example using strictly valid YAML and lowercase keys. Notes below it will explain that optional lines may be omitted; that `issue`, `tracking`, and `queue` are optional; that an active change requires `issue`; that a linked external issue requires `tracking`; that a tracker prefix is optional; and that an empty queue is omitted. This keeps the example readable while giving agents the decision rules needed to construct the file.

The template will name `send_file_content` exactly as the MCP tool, use `{{workflow.file}}` instead of the ambiguous “this file,” remove the redundant phase-transition reminder, and use the heading “Workflow State File Format”.

## Risks / Trade-offs

- [The format arrives only after the agent submits the workflow file] -> It improves otherwise empty file-content responses without changing the separate bootstrap-instruction flow.
- [A rendered response can hide the cache acknowledgement] -> This is intentional for a rendered workflow response and matches existing semantic-change behavior.
- [Copying disposition changes the serialized shape of aggregated rendered responses] -> Add focused event-aggregation assertions for both single and combined content.
- [Formatter updates code blocks across archived documents] -> Restrict the cleanup to Ruff-reported documents and verify the formatter is clean afterward.
