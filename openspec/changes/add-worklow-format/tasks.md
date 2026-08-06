## 1. Workflow Response Tests

- [ ] 1.1 Add a failing workflow-monitoring test showing that successfully parsed workflow content with no semantic change returns rendered state-format content through `send_file_content`.
- [ ] 1.2 Add failing assertions that the fallback response preserves the state-format instruction and `agent/instruction` disposition.
- [ ] 1.3 Add failing tests for a `None` state-format render and for semantic-change response precedence.
- [ ] 1.4 Add rendered-template assertions for the workflow state-format heading, field guidance, and `send_file_content` MCP-tool instruction.

## 2. Workflow Format Response

- [ ] 2.1 Render `state-format` after successful workflow parsing when no semantic workflow-change response exists, and use a non-`None` render as the response override.
- [ ] 2.2 Preserve rendered workflow content disposition when `TaskManager.process_result` replaces a response.
- [ ] 2.3 Keep workflow-disabled and semantic-change behavior unchanged when the fallback does not apply.

## 3. Workflow State-Format Template

- [ ] 3.1 Rename the heading to “Workflow State File” and revise the YAML example to use `description: <optional-description>`.
- [ ] 3.2 Add concise notes covering optional `issue`, `tracking`, and `queue` fields; active-change requirements; the optional tracker prefix; and omission of empty queues.
- [ ] 3.3 Replace the filesystem-tools wording with `send_file_content` MCP-tool guidance, refer to `{{workflow.file}}`, and remove the redundant phase-transition instruction.

## 4. Verification

- [ ] 4.1 Run focused workflow-monitoring, template-rendering, and filesystem response tests.
- [ ] 4.2 Run `uv run ruff format --check`, `uv run ruff check`, `uv run ty check`, and the relevant pytest suite.
