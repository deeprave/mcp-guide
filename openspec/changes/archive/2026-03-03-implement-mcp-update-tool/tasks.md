## 1. Preparation
- [x] 1.1 Review existing installer code (`installer/core.py`, `installer/integration.py`)
- [x] 1.2 Review existing task implementations (`openspec/task.py`, `workflow/tasks.py`)
- [x] 1.3 Review feature flag validation code

## 2. Rename Function
- [x] 2.1 Rename `update_templates()` to `update_documents()` in `installer/core.py`
- [x] 2.2 Update all references in `scripts/mcp_guide_install.py`
- [x] 2.3 Update all references in tests
- [x] 2.4 Run tests to confirm no breakage

## 3. Add Docroot Safety Check
- [x] 3.1 Add safety check function to `installer/core.py`
- [x] 3.2 Check `docroot.resolve(strict=True)` != template source path
- [x] 3.3 Raise exception if paths match
- [x] 3.4 Add to both `install_templates()` and `update_documents()`
- [x] 3.5 Add to `mcp-install` script
- [x] 3.6 Write tests for safety check (same path raises, different path ok)

## 4. Add Docroot Creation
- [x] 4.1 Add `await AsyncPath(docroot).mkdir(parents=True, exist_ok=True)` at start of `install_templates()`
- [x] 4.2 Add `await AsyncPath(docroot).mkdir(parents=True, exist_ok=True)` at start of `update_documents()`
- [x] 4.3 Ensures docroot exists before any file operations or locking
- [x] 4.4 Run tests to confirm no breakage

## 5. Add Feature Flag Validation
- [x] 5.1 Add `FLAG_AUTOUPDATE` constant to `feature_flags/constants.py`
- [x] 5.2 Add validation logic to reject project-level `autoupdate` flag
- [x] 5.3 Write tests for flag validation (global ok, project error)

## 6. Create Update Tool
- [x] 6.1 Create `tools/tool_update.py` with `update_documents` tool
- [x] 6.2 Ensure docroot exists: `await AsyncPath(docroot).mkdir(parents=True, exist_ok=True)`
- [x] 6.3 Create lock path: `lock_path = docroot / ".update"` (creates `.update.lock`)
- [x] 6.4 Implement version comparison logic (missing/differs/matches)
- [x] 6.5 Use `lock_update(lock_path, _perform_update, docroot, archive_path)`
- [x] 6.6 Return appropriate Result (success with stats or error)
- [x] 6.7 Write unit tests for tool logic
- [x] 6.8 Write integration test for tool execution

## 7. Update mcp-install Script
- [x] 7.1 Update `update` command to ensure docroot exists before locking
- [x] 7.2 Use same lock path: `docroot / ".update"`
- [x] 7.3 Verify lock is shared between tool and script

## 8. Create Update Task
- [x] 8.1 Create `tasks/update_task.py` with `McpUpdateTask`
- [x] 8.2 Implement `on_init()` to check `autoupdate` flag once
- [x] 8.3 Queue instruction if flag is true, then unsubscribe
- [x] 8.4 Unsubscribe immediately if flag is false/absent
- [x] 8.5 Skip if first-time install ran in session
- [x] 8.6 Write unit tests for task behavior
- [x] 8.7 Write integration test for task initialization

## 9. Create Instruction Template
- [x] 9.1 Create `_update.mustache` template
- [x] 9.2 Template directs agent to run `update_documents` tool
- [x] 9.3 Template explains update is available

## 10. Integration and Testing
- [x] 10.1 Run all tests to ensure no regressions
- [x] 10.2 Test update tool manually with different version scenarios
- [x] 10.3 Test autoupdate flag behavior at startup
- [x] 10.4 Verify lock cleanup on success and error paths
- [x] 10.5 Verify `.version` and `.original.zip` created after update
- [x] 10.6 Test docroot safety check (same path raises exception)
- [x] 10.7 Test concurrent updates (tool vs script) to ensure they wait for the lock
- [x] 10.8 Verify lock file created at `{docroot}/.update.lock`

## 11. Documentation
- [x] 11.1 Update tool documentation
- [x] 11.2 Update feature flag documentation
- [x] 11.3 Add usage examples
