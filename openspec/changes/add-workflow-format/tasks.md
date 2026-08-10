## 1. Workflow Response Tests

- [x] 1.1 Add a failing workflow-monitoring test showing that successfully parsed workflow content with no semantic change returns rendered state-format content through `send_file_content`.
- [x] 1.2 Add failing assertions that the fallback response preserves the state-format instruction and `agent/instruction` disposition.
- [x] 1.3 Add failing tests for a `None` state-format render and for semantic-change response precedence.
- [x] 1.4 Add rendered-template assertions for the “Workflow State File Format” heading, strict-YAML and lowercase-key guidance, optional-line omission, and exact `send_file_content` MCP-tool instruction.

## 2. Workflow Format Response

- [x] 2.1 Render `state-format` after successful workflow parsing when no semantic workflow-change response exists, and use a non-`None` render as the response override.
- [x] 2.2 Preserve rendered workflow content disposition when `TaskManager.process_result` replaces a response.
- [x] 2.3 Keep workflow-disabled and semantic-change behavior unchanged when the fallback does not apply.

## 3. Workflow State-Format Template

- [x] 3.1 Rename the heading to “Workflow State File Format” and revise the YAML example to use `description: <optional-description>`.
- [x] 3.2 Add concise notes that the file is strictly YAML with lowercase keys, optional lines may be omitted, and cover optional `issue`, `tracking`, and `queue` fields; active-change requirements; the optional tracker prefix; and omission of empty queues.
- [x] 3.3 Replace the filesystem-tools wording with `send_file_content` MCP-tool guidance, refer to `{{workflow.file}}`, and remove the redundant phase-transition instruction.

## 4. Verification

- [x] 4.1 Run focused workflow-monitoring, template-rendering, and filesystem response tests.
- [x] 4.2 Run `uv run ruff format --check`, `uv run ruff check`, `uv run ty check`, and the relevant pytest suite.

## 5. Documentation Formatting

- [x] 5.1 Apply Ruff formatting to the 34 currently reported Markdown documents, including archived OpenSpec artifacts, ADRs, and source READMEs, without changing their prose or behavior.
- [x] 5.2 Verify `uv run ruff format --check` reports no remaining document-formatting issues.
