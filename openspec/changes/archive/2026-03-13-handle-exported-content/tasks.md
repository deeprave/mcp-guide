## 1. Research Phase
- [x] 1.1 Research AI agents with semantic indexing capabilities (Claude, GitHub Copilot, etc.)
- [x] 1.2 Document indexing patterns and tool availability

## 2. Template Infrastructure
- [x] 2.1 Create `src/mcp_guide/templates/_system/` directory
- [x] 2.2 Move `_startup.mustache` to `_system/_startup.mustache`
- [x] 2.3 Move `_update.mustache` to `_system/_update.mustache`
- [x] 2.4 Update template discovery to recognize `_system/` category
- [x] 2.5 Create `_system/_export.mustache` template with conditional logic

## 3. Export Template Design
- [x] 3.1 Design template context structure (export.path, export.force, export.exists, export.expression, export.pattern)
- [x] 3.2 Add knowledge indexing detection logic to template
- [x] 3.3 Add conditional instructions for kiro/q-dev knowledge tool
- [x] 3.4 Add fallback instructions for direct file access
- [x] 3.5 Add instructions for other agents with indexing capabilities (if found)
- [x] 3.6 Add conditional logic for get_content export references vs export_content instructions

## 4. Add force parameter to get_content
- [x] 4.1 Add optional `force` boolean parameter to ContentArgs (default False)
- [x] 4.2 Implement export check in get_content (when force=False)
- [x] 4.3 Return reference instructions when content is exported (unless force=True)
- [x] 4.4 Render reference instructions via `_system/_export.mustache` template

## 5. Refactor export_content
- [x] 5.1 Remove hardcoded instruction string from export_content
- [x] 5.2 Add template rendering call with appropriate context
- [x] 5.3 Pass context variables to template (export.path, export.force, export.exists, export.expression, export.pattern)
- [x] 5.4 Ensure backward compatibility with existing behavior

## 6. Review Checkpoint
- [x] 6.1 Manual Verification
- [x] 6.2 Approval Gate

## 7. Testing
- [x] 7.1 Update tests for moved templates (_startup, _update)
- [x] 7.2 Add tests for export template rendering
- [x] 7.3 Test knowledge indexing instructions for kiro/q-dev
- [x] 7.4 Test fallback instructions when knowledge unavailable
- [x] 7.5 Test get_content with force=False (default)
- [x] 7.6 Test get_content with force=True
- [x] 7.7 Test get_content returns reference when content is exported
- [x] 7.8 Integration test for full export flow

## 8. Check Phase
- [x] 8.1 Run full test suite
- [x] 8.2 Run ruff check and mypy
- [x] 8.3 Manual testing of export with different scenarios
- [x] 8.4 Manual testing of get_content with and without force parameter
