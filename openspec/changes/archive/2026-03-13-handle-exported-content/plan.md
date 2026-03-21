# Implementation Plan: handle-exported-content

## Overview
Replace hardcoded export instructions with template-based rendering, add force parameter to get_content, and create _system template category for system-level templates.

## Phase 1: Research & Documentation
**Goal**: Document AI agents with semantic indexing capabilities

### 1.1 Research AI Agents
- Research kiro/q-dev knowledge tool capabilities
- Research Claude, GitHub Copilot, and other major AI agents
- Document which agents support semantic indexing
- Document tool names and detection methods

### 1.2 Document Findings
- Create research notes in change directory
- Document indexing patterns for each agent
- Note any special requirements or limitations

## Phase 2: Template Infrastructure
**Goal**: Create _system category and migrate existing templates

### 2.1 Create _system Directory
- Create `src/mcp_guide/templates/_system/` directory
- Verify directory is created successfully

### 2.2 Move Existing Templates
- Move `_startup.mustache` → `_system/_startup.mustache`
- Move `_update.mustache` → `_system/_update.mustache`
- Verify templates still render correctly

### 2.3 Update Template Discovery
- Review template discovery code
- Ensure `_system/` category is recognized
- Test that moved templates are discoverable

### 2.4 Update Template References
- Find all references to `_startup.mustache`
- Find all references to `_update.mustache`
- Update references to use new paths
- Run tests to verify no breakage

## Phase 3: Create Export Template
**Goal**: Design and implement _system/_export.mustache

### 3.1 Design Template Context
Context structure:
```
export:
  path: string          # Resolved export path
  force: boolean        # Whether to overwrite
  exists: boolean       # Existing export entry
  expression: string    # Content expression
  pattern: string|null  # Optional pattern filter
```

### 3.2 Create Template File
- Create `src/mcp_guide/templates/_system/_export.mustache`
- Add frontmatter with type: agent/instruction
- Add basic structure with conditionals

### 3.3 Implement Conditional Logic
Template sections:
1. **Export Content Instructions** (when called from export_content)
   - Check export.force for overwrite vs create
   - Provide file write instructions

2. **Get Content References** (when called from get_content)
   - Check for knowledge tool availability
   - Provide knowledge base instructions (kiro/q-dev)
   - Fallback to direct file path

3. **Agent-Specific Instructions**
   - Add conditionals for other agents with indexing
   - Provide appropriate instructions per agent

### 3.4 Test Template Rendering
- Create test cases for template rendering
- Test with various context combinations
- Verify conditional logic works correctly

## Phase 4: Add Force Parameter to get_content
**Goal**: Enable bypassing export check in get_content

### 4.1 Update ContentArgs
- Add `force: bool = False` to ContentArgs dataclass
- Update docstring to document parameter
- Verify type hints are correct

### 4.2 Implement Export Check
In `get_content` function:
1. Check if force=False (default)
2. Query project for export entry (expression, pattern)
3. If export entry exists and not forced:
   - Render `_system/_export.mustache` with context
   - Return reference instructions
4. Otherwise proceed with normal content retrieval

### 4.3 Build Template Context
When export entry found:
```python
context = {
    "export": {
        "path": export_entry.path,
        "force": False,
        "exists": True,
        "expression": args.expression,
        "pattern": args.pattern,
    }
}
```

### 4.4 Render Reference Instructions
- Call template renderer with `_system/_export.mustache`
- Pass context with export data
- Return rendered instructions to agent

## Phase 5: Refactor export_content
**Goal**: Replace hardcoded instruction with template rendering

### 5.1 Remove Hardcoded String
- Locate hardcoded instruction in export_content
- Remove the conditional string building
- Keep all other logic intact

### 5.2 Build Template Context
After export completes:
```python
context = {
    "export": {
        "path": output_path,
        "force": args.force,
        "exists": export_entry is not None,
        "expression": args.expression,
        "pattern": args.pattern,
    }
}
```

### 5.3 Render Template
- Call template renderer with `_system/_export.mustache`
- Pass context with export data
- Use rendered output as instruction

### 5.4 Verify Backward Compatibility
- Ensure instruction format matches previous behavior
- Run existing tests to verify no breakage
- Check that all scenarios still work

## Phase 6: Review Checkpoint
**Goal**: User review and verification before proceeding to comprehensive testing

### 6.1 Manual Verification
User to verify:
- Export content instructions render correctly
- Get content returns references when expected
- Get content with force=True returns full content
- Template rendering works as expected
- No regressions in existing functionality

### 6.2 Approval Gate
**STOP HERE** - Do not proceed to Phase 7 without explicit user approval

User should test:
1. Export content to file
2. Call get_content for exported expression
3. Call get_content with force=True
4. Verify instructions are appropriate
5. Check that existing workflows still function

Once approved, proceed to Phase 7 for comprehensive testing.

## Phase 7: Testing
**Goal**: Comprehensive test coverage for all changes

### 7.1 Template Migration Tests
- Test `_startup.mustache` renders from new location
- Test `_update.mustache` renders from new location
- Verify template discovery finds _system templates

### 7.2 Export Template Tests
- Test export_content instruction rendering
- Test get_content reference rendering
- Test force=True vs force=False behavior
- Test with/without export.pattern

### 7.3 Knowledge Indexing Tests
- Mock kiro/q-dev knowledge tool detection
- Verify correct instructions for knowledge indexing
- Test fallback when knowledge unavailable

### 7.4 Force Parameter Tests
- Test get_content with force=False (default)
- Test get_content with force=True
- Test get_content returns reference when exported
- Test get_content returns content when not exported

### 7.5 Integration Tests
- Test full export → get_content flow
- Test export with force → get_content
- Test multiple exports with different patterns
- Test staleness detection still works

## Phase 8: Check
**Goal**: Verify all quality checks pass

### 8.1 Run Test Suite
```bash
uv run pytest
```
- All tests must pass
- No regressions allowed

### 8.2 Run Code Quality Checks
```bash
uv run ruff check src tests
uv run mypy src
```
- No linting errors
- No type errors

### 8.3 Manual Testing
Test scenarios:
1. Export content → verify instructions
2. Get content (exported) → verify reference
3. Get content with force=True → verify full content
4. Export with force=True → verify overwrite instruction
5. Verify knowledge tool instructions appear (if available)

### 8.4 Verify Template Discovery
- Check _system templates are discoverable
- Verify underscore prefix makes them invisible to category_list_files
- Test that all template references work

## Success Criteria
- [ ] All tests pass
- [ ] Ruff and mypy pass with no errors
- [ ] Template-based instructions match previous hardcoded behavior
- [ ] Force parameter works correctly in get_content
- [ ] Export references reduce token usage
- [ ] Knowledge indexing instructions appear when available
- [ ] Backward compatibility maintained
