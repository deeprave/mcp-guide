# Implementation Plan: add-export-tools

## Overview
Add export management tools (`list_exports`, `remove_export`) and reorganize export commands under `_commands/export/` directory.

## Architecture Decisions
None required - extends existing export tracking infrastructure in `Project.exports`.

## Implementation Approach

### Phase 0: Tool Stubs (Verification Checkpoint)
Create minimal tool stubs and verify MCP initialization before proceeding with full implementation.

### Phase 1: Tool Implementation (TDD)
Implement tools using test-driven development following Red-Green-Refactor cycle.

### Phase 2: Command Templates
Create command templates and formatting template for user-facing display.

### Phase 3: Integration & Testing
Full integration testing and manual verification of complete export workflow.

## Detailed Tasks

### 0. Tool Stubs (Verification Checkpoint)

#### 0.1 Create tool stubs
- Add `ListExportsArgs` dataclass with optional `glob: Optional[str]` parameter
- Add `list_exports()` async function that returns empty list `[]`
- Add `RemoveExportArgs` dataclass with `expression: str` and optional `pattern: Optional[str]`
- Add `remove_export()` async function that returns `Result.ok("Not implemented")`
- Register both tools in tool infrastructure

#### 0.2 Verify MCP initialization
- Restart MCP server
- Verify server initializes without errors
- Verify both tools appear in tool list
- **STOP HERE** - Wait for user confirmation before proceeding with implementation

### 1. list_exports Tool (TDD)

#### 1.1 RED: Test empty exports
- Write test: `test_list_exports_empty()` - expects empty array when no exports exist
- Run test → FAIL

#### 1.2 GREEN: Implement basic list_exports
- Add `ListExportsArgs` dataclass with optional `glob` parameter
- Add `list_exports()` async function that returns empty list
- Register tool in tool infrastructure
- Run test → PASS

#### 1.3 RED: Test single export
- Write test: `test_list_exports_single()` - expects array with one export entry
- Mock `Project.exports` with one entry
- Run test → FAIL

#### 1.4 GREEN: Implement export iteration
- Iterate `Project.exports` dict
- Build list of dicts with expression, pattern, path fields
- Run test → PASS

#### 1.5 RED: Test timestamp extraction
- Write test: `test_list_exports_with_timestamp()` - expects exported_at from file mtime
- Mock file stat to return mtime
- Run test → FAIL

#### 1.6 GREEN: Implement timestamp extraction
- Use `aiofiles.os.stat()` to get file mtime
- Convert to ISO timestamp
- Handle missing/unreadable files (return null)
- Run test → PASS

#### 1.7 RED: Test staleness detection
- Write test: `test_list_exports_staleness()` - expects stale=true when source changed
- Mock `discover_documents()` to return different mtimes
- Run test → FAIL

#### 1.8 GREEN: Implement staleness detection
- Call `discover_documents()` for expression/pattern
- Compute metadata_hash from file list
- Compare to stored hash
- Set stale boolean
- Run test → PASS

#### 1.9 RED: Test glob filtering
- Write test: `test_list_exports_glob_filter()` - expects filtered results
- Test matching expression, pattern, and path
- Run test → FAIL

#### 1.10 GREEN: Implement glob filtering
- Use `fnmatch` for case-insensitive glob matching
- Filter exports against expression, pattern, path
- Run test → PASS

#### 1.11 REFACTOR: Extract helper functions
- Extract `_get_export_timestamp()` helper
- Extract `_compute_staleness()` helper
- Extract `_matches_glob()` helper
- Run all tests → PASS

### 2. remove_export Tool (TDD)

#### 2.1 RED: Test successful removal
- Write test: `test_remove_export_success()` - expects Result.ok
- Mock `Project.exports` with entry to remove
- Run test → FAIL

#### 2.2 GREEN: Implement basic remove_export
- Add `RemoveExportArgs` dataclass with expression and optional pattern
- Add `remove_export()` async function
- Remove entry from `Project.exports` via session.update_config()
- Return Result.ok
- Run test → PASS

#### 2.3 RED: Test not found error
- Write test: `test_remove_export_not_found()` - expects Result.failure with error_type="not_found"
- Run test → FAIL

#### 2.4 GREEN: Implement not found handling
- Check if key exists in `Project.exports`
- Return Result.failure if not found
- Run test → PASS

#### 2.5 RED: Test expression-only removal
- Write test: `test_remove_export_no_pattern()` - expects removal of (expression, None) key
- Run test → FAIL

#### 2.6 GREEN: Handle None pattern
- Build key as `(expression, None)` when pattern not provided
- Run test → PASS

#### 2.7 REFACTOR: Simplify key construction
- Extract key building logic
- Add descriptive error messages
- Run all tests → PASS

### 3. Command Templates

#### 3.1 Reorganize export command
- Create `src/mcp_guide/templates/_commands/export/` directory
- Move existing export command to `export/add.mustache`
- Add frontmatter with `alias: export`
- Verify command discovery finds both `:export` and `:export/add`

#### 3.2 Create list command
- Create `_commands/export/list.mustache`
- Add frontmatter: type=agent/instruction, argrequired for optional glob
- Instruction: call `list_exports` tool with optional glob parameter
- Reference `_system/_exports-format.mustache` for formatting

#### 3.3 Create remove command
- Create `_commands/export/remove.mustache`
- Add frontmatter: type=agent/instruction, argrequired for expression and pattern
- Instruction: call `remove_export` tool with expression and pattern
- Display success/error message

#### 3.4 Create formatting template
- Create `_system/_exports-format.mustache`
- Add frontmatter: type=user/information
- Format export list as markdown table or list
- Show expression, pattern, path, timestamp
- Highlight stale exports with ⚠️ marker
- Handle empty list case

### 4. Integration & Testing

#### 4.1 Unit test coverage
- Verify all tool tests pass
- Check edge cases: missing files, invalid globs, concurrent modifications
- Ensure error paths tested

#### 4.2 Command discovery tests
- Test `:export`, `:export/add`, `:export/list`, `:export/remove` all discovered
- Verify alias resolution
- Check argrequired parsing

#### 4.3 Template rendering tests
- Test `_exports-format.mustache` with various data
- Verify empty list message
- Check stale indicator display

#### 4.4 Run full test suite
- `uv run pytest` - all tests must pass
- `uv run ruff check src tests` - no warnings
- `uv run mypy src` - no type errors

#### 4.5 Manual testing
- Export some content with `export_content`
- List exports with `:export/list`
- Verify timestamps and staleness
- Filter with glob pattern
- Remove export with `:export/remove`
- Verify removal successful
- Test error cases (not found, invalid args)

## Dependencies
- Existing: `Project.exports`, `discover_documents()`, `export_content` tool
- New: None

## Success Criteria
- All tests pass (unit, integration, type checking, linting)
- Commands accessible as `:export`, `:export/add`, `:export/list`, `:export/remove`
- `list_exports` returns accurate metadata including staleness
- `remove_export` removes tracking without deleting files
- Glob filtering works correctly
- Templates render properly
- Manual workflow verification complete
