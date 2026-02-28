## 1. Preparation
- [ ] 1.1 Review existing installer code (`installer/core.py`, `installer/integration.py`)
- [ ] 1.2 Review existing task implementations (`openspec/task.py`, `workflow/tasks.py`)
- [ ] 1.3 Review feature flag validation code

## 2. Rename Function
- [ ] 2.1 Rename `update_templates()` to `update_docs()` in `installer/core.py`
- [ ] 2.2 Update all references in `scripts/mcp_guide_install.py`
- [ ] 2.3 Update all references in tests
- [ ] 2.4 Run tests to confirm no breakage

## 3. Add Docroot Safety Check
- [ ] 3.1 Add safety check function to `installer/core.py`
- [ ] 3.2 Check `docroot.resolve(strict=True)` != template source path
- [ ] 3.3 Raise exception if paths match
- [ ] 3.4 Add to both `install_templates()` and `update_docs()`
- [ ] 3.5 Add to `mcp-install` script
- [ ] 3.6 Write tests for safety check (same path raises, different path ok)

## 4. Add Feature Flag Validation
- [ ] 4.1 Add `FLAG_AUTOUPDATE` constant to `feature_flags/constants.py`
- [ ] 4.2 Add validation logic to reject project-level `autoupdate` flag
- [ ] 4.3 Write tests for flag validation (global ok, project error)

## 5. Create Update Tool
- [ ] 5.1 Create `tools/tool_update.py` with `update_documents` tool
- [ ] 5.2 Implement version comparison logic (missing/differs/matches)
- [ ] 5.3 Use `lock_update()` for exclusive access
- [ ] 5.4 Call `update_docs()` with session docroot
- [ ] 5.5 Return appropriate Result (success with stats or error)
- [ ] 5.6 Write unit tests for tool logic
- [ ] 5.7 Write integration test for tool execution

## 6. Create Update Task
- [ ] 6.1 Create `tasks/mcp_update_task.py` with `McpUpdateTask`
- [ ] 6.2 Implement `on_init()` to check `autoupdate` flag once
- [ ] 6.3 Queue instruction if flag is true, then unsubscribe
- [ ] 6.4 Unsubscribe immediately if flag is false/absent
- [ ] 6.5 Skip if first-time install ran in session
- [ ] 6.6 Write unit tests for task behavior
- [ ] 6.7 Write integration test for task initialization

## 7. Create Instruction Template
- [ ] 7.1 Create `_commands/update-prompt.mustache` template
- [ ] 7.2 Template directs agent to run `update_documents` tool
- [ ] 7.3 Template explains update is available

## 8. Integration and Testing
- [ ] 8.1 Run all tests to ensure no regressions
- [ ] 8.2 Test update tool manually with different version scenarios
- [ ] 8.3 Test autoupdate flag behavior at startup
- [ ] 8.4 Verify lock cleanup on success and error paths
- [ ] 8.5 Verify `.version` and `.original.zip` created after update
- [ ] 8.6 Test docroot safety check (same path raises exception)

## 9. Documentation
- [ ] 9.1 Update tool documentation
- [ ] 9.2 Update feature flag documentation
- [ ] 9.3 Add usage examples
