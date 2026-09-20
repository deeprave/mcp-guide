## Context

See proposal.md - Why. Relevant current-code facts:

- `OpenSpecTask._is_enabled()` gates the whole detection flow on the `openspec` project flag; unaffected by this change.
- The current two-stage flow: `FS_COMMAND` handler (`task.py:338-359`) receives `{command, path, found}` from `send_command_location`, sets `_available`, and — only if `found` — triggers `request_version_check()`, which renders `openspec-version-check.mustache` and queues it. The response arrives via `FS_FILE_CONTENT` matched on `path_name == ".openspec-version.txt"` (`task.py:409-418`), calling `_parse_version(content)`.
- `_parse_version` (`task.py:499-529`) regex-extracts a semantic version (`v?(\d+\.\d+\.\d+)`) from the raw command output, sets `validated=True` only on a successful match, `validated=False` otherwise, and — only on success — triggers the next stage, `request_project_check()`.
- `_persist_global_state(validated, version=None)` writes through to `OpenSpecState`/`serialise_openspec_state` (`src/mcp_guide/openspec/state.py`), which stores `{validated: "true"|"false", checked: <timestamp-str>, version?: <str>}` as the `openspec-state` global feature flag. This persistence contract must not change.
- `send_command_location`'s Pydantic args (`SendCommandLocationArgs` in `tool_filesystem.py`) are `command: str`, `location: Optional[str]` — generic, used by other detection flows beyond OpenSpec; per the user's explicit correction this session, it must stay generic and must not gain an OpenSpec-specific `version` field.
- `send_file_content`'s args (`SendFileContentArgs`) already have a plain `content: str` field with no fixed internal structure — the existing `.openspec-changes.json`/`.openspec-status.json` synthetic paths already send JSON as that string, so a structured payload for the combined check is a proven pattern, not a new one.
- Test files affected: `tests/test_openspec_task.py` and `tests/unit/test_openspec_task_ack.py` test actual detection/acknowledgement behavior and need updating; `tests/unit/test_project_task_activation.py` only needs a fixture filename rename (see proposal.md - Impact).

## Goals / Non-Goals

**Goals:**
- One shell command, one tool call, one server-side event, replacing the current two of each.
- Preserve the exact `openspec-state` output contract (`validated`/`version`/`checked` semantics) so no downstream consumer (feature-flag resolution, `_build_openspec_context` in `render/cache.py`) needs to change.
- Keep `send_command_location` generic and unmodified.
- Cooperative, why/what/where instruction wording, consistent with `_filesystem-probe.mustache`/`_project-root.mustache`.

**Non-Goals:**
- Changing how `openspec-state` is consumed downstream (feature-flag resolution, template context, version-gated feature checks) — only how it's produced.
- Changing the unrelated `.openspec-changes.json`/`.openspec-status.json` synthetic-path flows.
- Combining OpenSpec's third stage (project-structure detection, `openspec-project-check.mustache` / `FS_DIRECTORY`) into this same round trip — that remains a separate, subsequent request, since it depends on a *validated* CLI and answers a materially different question (is this specific project OpenSpec-initialized) than "is the CLI installed."

## Decisions

### Combined shell check: `openspec --version` alone, with a location fallback only on failure

**Decision:** The combined instruction asks the agent to run `openspec --version`. If it succeeds (nonzero-length output, zero exit status), that output alone provides both "found" (implicitly — the command ran) and "version" (parsed from the output). Only if that fails does the instruction ask the agent to additionally check `which`/`where openspec` to distinguish "not on PATH" from "on PATH but erroring" for diagnostic purposes — reported as `location: null` either way from the caller's perspective, since both are equally "not usable."

**Why:** `openspec --version` is the single command that answers the question this whole flow exists to answer ("what version is available, if any") in the common case, avoiding a separate existence probe for the majority of successful runs. The fallback to `which`/`where` is diagnostic-only (useful in logs/troubleshooting, not required for the `openspec-state` flag itself, which only needs `validated`/`version`).

**Alternatives considered:** `which openspec && openspec --version` unconditionally (two commands, still one round trip) — rejected as strictly more work than needed in the common case where the CLI is present and working; `openspec --version` alone already tells you it's on PATH by virtue of running successfully.

### Combined report format: JSON content on `.openspec-info.json`

**Decision:** Rename the synthetic routing path from `.openspec-version.txt` to `.openspec-info.json`. Its `content` is a JSON object carrying `location` (path string, or `null` if not found) and `version` (raw `openspec --version` output, or `null` if the command failed), parsed with `json.loads` — the same approach the `FS_FILE_CONTENT` handler already uses for `.openspec-changes.json` and `.openspec-status.json`. The version substring is still extracted from `version` server-side with the existing semantic-version regex, so a raw, unparsed CLI output string (e.g. `"openspec/1.13.1"`) remains acceptable input; JSON only structures the *envelope* (which field is which), not the version string's own format.

**Why:** `.json`-suffixed synthetic paths with real JSON content are already this handler's established convention (`.openspec-changes.json`, `.openspec-status.json`) — using `key: value` lines instead would have introduced a second, inconsistent format next to that convention for no benefit. JSON is also unambiguous regardless of what characters a real-world version string contains, and `json` is already imported and used in this exact code path (`task.py`'s `FS_FILE_CONTENT` handler).

**Alternatives considered:** Plain `key: value` lines — initially proposed here, but rejected on review since it would have been a second, inconsistent structured-content convention alongside the existing JSON one for no real benefit.

### Task state: collapse two request/ack pairs into one

**Decision:** Replace `_cli_requested`/`_version_requested`/`_cli_instruction_id`/`_version_instruction_id` with a single `_detection_requested`/`_detection_instruction_id` pair. `request_cli_check()` and `request_version_check()` collapse into a single `request_detection()`. The `FS_COMMAND` handler is removed for this flow; only the `FS_FILE_CONTENT` handler on `.openspec-info.json` remains, replacing the current `.openspec-version.txt` handler and absorbing the location-parsing logic currently in the `FS_COMMAND` branch.

**Why:** Directly mirrors the round-trip reduction — one request, one acknowledgement, one piece of state tracking it.

**Alternatives considered:** Keep both instruction-ID fields for backward-compatible internal bookkeping even though only one request now fires — rejected as unnecessary complexity once there is genuinely only one instruction in flight.

## Risks / Trade-offs

- **[Risk]** Collapsing "not found" and "found but unparseable version" into a single combined handler could accidentally conflate two states that currently have distinct code paths (`FS_COMMAND`'s direct `_persist_global_state(validated=False)` vs. `_parse_version`'s fallback branch). → **Mitigation:** the spec's "Distinguishes not-found, found-without-version, and found-with-version" requirement explicitly names all three outcomes with their own scenarios, so the implementation is checked against all three, not just the two the current split-handler code happens to produce.
- **[Risk]** Renaming `.openspec-version.txt` to `.openspec-info.json` and switching its content from raw text to JSON is a wire-format break for anything expecting the old path/shape (unlikely given this is an internal agent-server protocol with no persisted external contract, but worth naming). → **Mitigation:** this is a pre-release internal protocol with no versioned external clients depending on the specific synthetic filename or content format; the rename and format change are safe within this project's compatibility model.

## Migration Plan

No data migration — `openspec-state`'s stored shape is unchanged; only how it gets populated changes. Sequencing: implement and test the combined flow, then remove the two old templates and the old two-stage task logic in the same change (no need to support both flows simultaneously, since this is a single-process in-memory detection flow with no persisted intermediate state to migrate).
