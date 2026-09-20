## Why

Detecting the OpenSpec CLI today costs the agent two separate shell commands and two separate tool round trips: `openspec-cli-check.mustache` asks for `which openspec` via the structured `send_command_location` tool, and only after the server sees a positive result does it fire a second instruction, `openspec-version-check.mustache`, asking for `openspec --version` via `send_file_content` with a synthetic `.openspec-version.txt` path. The version pathway repurposes a filesystem-content tool to carry a value that isn't file content at all, and neither instruction explains to the agent why the information is requested or where it ends up — a case of the same unexplained-imperative pattern already being addressed elsewhere for this project (see `_filesystem-probe.mustache` and `_project-root.mustache`, and the parallel `cooperative-result-disposition` change).

## What Changes

- Combine CLI-location and version detection into a single instruction and a single round trip: one shell invocation (exact form decided in design.md) answers both "is OpenSpec installed" and "what version," and the agent reports both together in one tool call.
- Keep `send_command_location(command, location)` unchanged and generic — it is used for reporting the location of any command, not just OpenSpec, and must not gain OpenSpec-specific fields (a version field on a generic tool would leak a domain-specific concern into shared infrastructure).
- Carry the combined result through `send_file_content`'s existing synthetic-path mechanism instead, renaming the routing key from `.openspec-version.txt` to `.openspec-info.json` and sending a JSON object carrying both `location` and `version` together — matching the JSON-content convention already established by this handler's other synthetic paths (`.openspec-changes.json`, `.openspec-status.json`) — replacing the two prior separate paths (`.openspec-version.txt`, and the location half of the exchange that previously went through `send_command_location`).
- Update `OpenSpecTask`'s internal state and event handling (`src/mcp_guide/openspec/task.py`) to issue one combined request and process one combined response, replacing the separate `_cli_requested`/`_version_requested` flags, `_cli_instruction_id`/`_version_instruction_id` tracking, and the two-stage `FS_COMMAND` → `FS_FILE_CONTENT` sequencing with a single `FS_FILE_CONTENT` round trip.
- Rewrite the combined instruction's wording in a cooperative, second-person, why/what/action style: state that Guide is checking for OpenSpec CLI availability and version because some OpenSpec-dependent features may be gated by version, and that the result is stored in the project's `openspec-state` feature flag (a global-only flag, confirmed this session via `list_feature_flags`/`list_project_flags` output — not project-overridable).
- Preserve unchanged: the `openspec` feature-flag gate on whether this check runs at all (`OpenSpecTask.start()`/`_is_enabled()`), and the downstream `OpenSpecState`/`parse_openspec_state`/`serialise_openspec_state` machinery and the `openspec-state` feature flag it populates.
- **BREAKING** (internal protocol only, no external API): the wire format for reporting OpenSpec CLI info to the server changes (new synthetic path, new content shape); this affects only the agent-server exchange for this one detection flow, not any client-facing tool signature.

## Capabilities

### New Capabilities
- `openspec-cli-detection`: Defines the combined CLI-location-and-version detection flow — when it runs, what the agent is asked to do, the wire format for reporting the combined result, and how the result populates `openspec-state`. (No existing spec covers this flow; the only prior OpenSpec-related spec content, `cache-management`, covers the unrelated changes-list caching TTL.)

### Modified Capabilities
(none — this is new capability documentation for previously-unspecified behavior, not a change to an existing requirement)

## Impact

- `src/mcp_guide/templates/_openspec/openspec-cli-check.mustache` and `openspec-version-check.mustache` — replaced by a single combined template.
- `src/mcp_guide/openspec/task.py` — `OpenSpecTask`'s request/response state and `FS_COMMAND`/`FS_FILE_CONTENT` event handling simplified to one combined exchange.
- No change to `send_command_location`'s tool signature (`src/mcp_guide/tools/tool_filesystem.py`) — it remains generic, used unchanged by every other command-location reporting flow in the codebase.
- `send_file_content`'s routing-key convention gains one new synthetic path (`.openspec-info.json`) replacing `.openspec-version.txt`, consistent in both naming and JSON content with the handler's existing `.openspec-changes.json`/`.openspec-status.json` paths; those existing unrelated synthetic paths are unaffected.
- Tests covering the two-stage detection sequence need updating for the combined single-stage flow: `tests/test_openspec_task.py` (substantive detection/persistence/response-handling behavior) and `tests/unit/test_openspec_task_ack.py` (parametrized acknowledgement-protocol coverage across check kinds, including `cli` and `version`) both exercise the current `_cli_requested`/`_version_requested`/`request_cli_check`/`request_version_check` state and flow directly. `tests/unit/test_project_task_activation.py` only needs its throwaway `openspec-cli-check.mustache` fixture stub renamed to match the combined template's filename — it tests generic task-activation machinery (shared with `ClientContextTask`, `WorkflowMonitorTask`), not OpenSpec-specific behavior, and is otherwise unaffected.
