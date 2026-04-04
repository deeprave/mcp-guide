## 1. Handle full path in switch_project
- [x] 1.1 Strip `file://` prefix if present
- [x] 1.2 Validate path is absolute — reject relative paths with clear error
- [x] 1.3 Validate path has no `..` traversal components (checked via `path.parts`)
- [x] 1.4 Extract `basename(path)` as the project name
- [x] 1.5 Update `self.roots` with a synthetic root from the provided path
- [x] 1.6 Proceed with the basename through existing `_NAME_REGEX` validation and binding

## 2. Consistent no-project error
- [x] 2.1 Define `RESULT_NO_PROJECT` as a static `Result` in `result_constants.py`
- [x] 2.2 Emphatic instruction text: context first, then MUST use set_project tool
- [x] 2.3 Replace all ad-hoc `Result.failure(..., error_type=ERROR_NO_PROJECT)` with `RESULT_NO_PROJECT`
- [x] 2.4 Add `requires_project` param to `toolfunc` decorator (default `True`)
- [x] 2.5 All tools except `set_project` return `RESULT_NO_PROJECT` when session is unbound

## 3. Resource handlers through TaskManager pipeline
- [x] 3.1 Resource handlers now go through `process_result` → `to_json_str()`
- [x] 3.2 `additional_agent_instructions` now surfaces on resource reads

## 4. Session registry lookup for cross-task persistence
- [x] 4.1 `get_or_create_session` checks `_session_registry` when ContextVar is empty
- [x] 4.2 Session bound by `set_project` persists across sibling async Tasks

## 5. Instruction clarity
- [x] 5.1 Status template: conditional instruction based on workflow state
- [x] 5.2 Monitoring templates: emphatic `send_file_content` tool instructions
- [x] 5.3 Tracking doc: uses `{{tool_prefix}}send_file_content` tool reference

## 6. Validation
- [x] 6.1 Full path like `/Users/davidn/Code/mcp-guide` resolves to project `mcp-guide`
- [x] 6.2 `file://` URI accepted and handled correctly
- [x] 6.3 Plain name continues to work unchanged
- [x] 6.4 Relative paths rejected with clear error
- [x] 6.5 Paths with `..` traversal rejected with clear error
- [x] 6.6 All tools return consistent error when project is unbound
- [x] 6.7 Codex end-to-end: set_project, status, workflow all functional
