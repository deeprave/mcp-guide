## 1. Combined template

- [ ] 1.1 Create `src/mcp_guide/templates/_openspec/openspec-check.mustache` (replacing `openspec-cli-check.mustache` and `openspec-version-check.mustache`) asking the agent to run `openspec --version`, with a `which`/`where` fallback only on failure, and report the combined result as JSON via `{{tool_prefix}}send_file_content` with path `.openspec-info.json` (e.g. `{"location": "...", "version": "..."}` with `null` for whichever half is unavailable). Wording SHALL be second-person, terse, and state why the check is requested and where the result is stored (`openspec-state` feature flag), per the style validated on `_filesystem-probe.mustache`/`_project-root.mustache`. Verify completion by rendering the template directly in a unit test and asserting it contains the why/where explanation and the correct tool/path names.
- [ ] 1.2 Delete `openspec-cli-check.mustache` and `openspec-version-check.mustache`. Verify completion by `grep -rn` confirming no remaining references to either filename in `src/` or `tests/`.

## 2. OpenSpecTask state and event handling

- [ ] 2.1 Replace `_cli_requested`/`_version_requested`/`_cli_instruction_id`/`_version_instruction_id` with `_detection_requested`/`_detection_instruction_id` in `OpenSpecTask.__init__`. Verify completion by the class no longer referencing the old field names anywhere.
- [ ] 2.2 Replace `request_cli_check()` and `request_version_check()` with a single `request_detection()` that renders `openspec-check` and queues it. Verify completion by a unit test asserting exactly one instruction is queued per detection cycle.
- [ ] 2.3 Remove the `FS_COMMAND` handling branch for `command == "openspec"`. Add a `FS_FILE_CONTENT` handler for `path_name == ".openspec-info.json"` that `json.loads` the content and parses both `location` and `version` (either may be `null`), covering all three outcomes: not found, found-but-unparseable-version, found-with-version. Verify completion by unit tests covering all three outcomes and asserting the correct `_persist_global_state(validated=..., version=...)` call for each.
- [ ] 2.4 Confirm `_persist_global_state`/`OpenSpecState`/`parse_openspec_state`/`serialise_openspec_state` remain unchanged and the `openspec-state` flag's stored shape (`validated`/`version`/`checked`) is identical before and after this change. Verify completion by an existing or new test asserting the flag's serialized shape matches the pre-change contract for at least one detected-version case.
- [ ] 2.5 Confirm the post-validation `request_project_check()` trigger (currently inside `_parse_version` on successful version parse) still fires correctly from the new combined handler. Verify completion by a test asserting project-structure detection is requested after a successful combined detection.

## 3. Test updates

- [ ] 3.1 Update `tests/test_openspec_task.py` for the combined single-stage flow (single request, single `FS_FILE_CONTENT` response, three-outcome coverage). Verify completion by the file's tests passing against the new implementation.
- [ ] 3.2 Update `tests/unit/test_openspec_task_ack.py`'s parametrized `check_kind` cases: collapse the separate `cli`/`version` parametrizations into one combined-detection case, keeping `project` as its own subsequent stage. Verify completion by the updated parametrization passing.
- [ ] 3.3 Rename the throwaway fixture stub in `tests/unit/test_project_task_activation.py` from `openspec-cli-check.mustache` to `openspec-check.mustache` (or whatever filename task 1.1 lands on). Verify completion by that one test still passing with no other changes needed.
- [ ] 3.4 Run the full test suite and confirm no regressions beyond the files touched above. Verify completion by a full `pytest` run reporting the expected pass count with no unrelated failures.

## 4. Final validation

- [ ] 4.1 Manually or via test harness, exercise the combined flow end-to-end (openspec CLI present with a real version) and confirm `openspec-state` ends up with the same shape as it did before this change for the equivalent scenario. Verify completion by comparing the resulting `openspec-state` feature-flag value against a captured pre-change baseline.
