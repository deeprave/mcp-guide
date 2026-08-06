## Context

`WorkflowMonitorTask` parses received workflow-file content and stores a rendered semantic-change response only when the parsed state differs from the cached state. Otherwise, `send_file_content` returns a cache acknowledgement. The internal `_workflow/state-format.mustache` template defines the format but is neither directly exposed through Guide nor rendered by the monitor.

`RenderedContent` retains the template's frontmatter-derived instruction and type. The existing workflow-change response replacement copies content and instruction into `Result`, but not its `disposition` field.

## Goals / Non-Goals

**Goals:**

- Return rendered workflow-format guidance in response to successfully parsed workflow-file content when no semantic-change response is available.
- Preserve the template's content, instruction, and `agent/instruction` disposition in the response.
- Leave disabled workflow behavior unchanged when `state-format` is filtered and renders as `None`.
- Preserve existing semantic workflow-change responses.
- Make the state-format template accurately document optional fields and the `send_file_content` MCP tool.

**Non-Goals:**

- Expose `_workflow/state-format.mustache` through a `guide://` URI.
- Change bootstrap or timer-driven queued instructions.
- Change the workflow state-file schema.

## Decisions

### Reuse the workflow response override path

When parsing succeeds and no semantic change response was rendered, `WorkflowMonitorTask` will render `state-format`. A non-`None` result will be stored through the existing `workflow_change_content` mechanism, causing the same `send_file_content` response to be replaced with rendered guidance.

This keeps workflow response selection inside the workflow monitor and avoids changing generic filesystem event aggregation. Returning `EventResult.rendered_content` directly would require aggregation to preserve the template disposition for every task event and would broaden the change beyond workflow handling.

### Preserve template disposition in `Result`

`TaskManager.process_result` will copy the selected rendered content's `template_type` into `Result.disposition` together with its content and instruction. This makes the response's agent-facing disposition match `state-format` frontmatter and also correctly represents existing synthesized workflow change content as `agent/instruction`.

### Render only as fallback

The state-format template is fallback guidance, not an addition to a semantic-change response. A detected state change continues to use its existing phase or monitoring response. A `None` format render produces no override, so the existing cache acknowledgement remains for workflow-disabled projects.

### Keep field conditions in prose below the YAML example

The YAML block will remain a compact structural example. Notes below it will explain that `issue`, `tracking`, and `queue` are optional; that an active change requires `issue`; that a linked external issue requires `tracking`; that a tracker prefix is optional; and that an empty queue is omitted. This keeps the example readable while giving agents the decision rules needed to construct the file.

The template will name `send_file_content` as an MCP tool, use `{{workflow.file}}` instead of the ambiguous “this file,” remove the redundant phase-transition reminder, and use the concise “Workflow State File” heading.

## Risks / Trade-offs

- [The format arrives only after the agent submits the workflow file] -> It improves otherwise empty file-content responses without changing the separate bootstrap-instruction flow.
- [A response override can hide the cache acknowledgement] -> This is intentional for a rendered workflow response and matches existing semantic-change behavior.
- [Copying disposition changes the serialized shape of existing workflow-change responses] -> Add focused assertions for both new fallback guidance and existing change responses.
