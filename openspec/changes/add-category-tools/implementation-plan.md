# Category Tools - TDD Implementation Plan

**Change:** add-category-tools
**Approach:** Test-Driven Development (Red-Green-Refactor)
**Dependencies:** tool-conventions (NEEDS REFACTOR), session management, config management

## Phase 0: Tool Registration Refactor ✅ COMPLETE

**Status:** ✅ COMPLETE - All phases 0.1-0.7 implemented and tested

**Summary:** Refactored from broken lazy constructor pattern to working decorator pattern with ContextVar test mode control.

**Key Changes:**
- Decorator-based registration with `@tools.tool(ArgsClass)`
- ContextVar test mode control (no external manipulation)
- _ToolsProxy for lazy initialization
- Tool signature: direct kwargs instead of args object
- Return type: JSON strings via `Result.to_json_str()`
- End-to-end MCP client integration test validates architecture

**Results:**
- ✅ 188 tests passing, 89% coverage
- ✅ Integration test proves tools work through MCP protocol
- ✅ All quality checks pass

### Phase 0.8: CLI Tool Prefix Control ✅ COMPLETE

**Requirement:** Add command line arguments to control tool prefix and logging configuration.

**Design:**
- `--tool-prefix PREFIX` - Set custom prefix (requires argument)
- `--no-tool-prefix` - Disable prefix entirely (flag)
- `--log-level LEVEL` - Set log level (TRACE|DEBUG|INFO|WARNING|ERROR)
- `--log-file PATH` - Set log file path
- `--log-json` - Enable JSON log format
- Default: "guide" prefix, INFO level, no file, no JSON
- Priority: CLI args > env var > default

**Implementation:**
- Created `src/mcp_guide/cli.py` with ServerConfig dataclass and parse_args()
- Updated `main.py` to use CLI configuration
- Click handles environment variable fallback automatically
- Mutually exclusive options (can't use both prefix options)

**Files Created:**
- `src/mcp_guide/cli.py` - CLI configuration module (31 statements, 100% coverage)
- `tests/unit/mcp_guide/test_cli.py` - 13 tests for CLI parsing

**Files Modified:**
- `src/mcp_guide/main.py` - Use parse_args() and ServerConfig
- `tests/test_main.py` - Updated for ServerConfig
- `tests/unit/mcp_guide/test_main_integration.py` - Updated for ServerConfig

**Results:**
- ✅ 200 tests passing, 89% coverage
- ✅ All CLI options work with envvar fallback
- ✅ Mutual exclusion enforced
- ✅ All quality checks pass

---

## Overview

Implement 5 category management tools following tool conventions with auto-save on every change.

## Phase 1: Validation Functions (Foundation) ✅ COMPLETE

### 1.1 Validation Infrastructure - REFACTORED ✅
- [x] Moved validation to `mcp_core` (generic, reusable)
- [x] Created `ValidationError(BaseException)` exception class
- [x] Added `error_type` (default: "validation_error")
- [x] Added `instruction` (default: DEFAULT_INSTRUCTION)
- [x] Applied DRY principles with string constants (ERR_*)
- [x] Exception-based validation (raises ValidationError)

### 1.2 Directory Path Validation ✅
- [x] Write test: valid relative path "docs/examples"
- [x] Write test: reject absolute path Unix "/absolute"
- [x] Write test: reject absolute path Windows "C:\\"
- [x] Write test: reject UNC path "\\\\server\\share"
- [x] Write test: reject traversal "../parent"
- [x] Write test: reject leading __ "__invalid/path"
- [x] Write test: reject trailing __ "path/__invalid"
- [x] Write test: default when None/empty
- [x] Implement `validate_directory_path(path: Optional[str], default: str) -> str`
- [x] Extract `is_absolute_path()` helper (Unix/Windows/UNC)
- [x] Raises ValidationError on invalid input

### 1.3 Description Validation ✅
- [x] Write test: valid description under 500 chars
- [x] Write test: reject over default 500 chars
- [x] Write test: custom max_length parameter
- [x] Write test: reject quotes (single and double)
- [x] Write test: allow empty/None
- [x] Implement `validate_description(desc: Optional[str], max_length: int = 500) -> Optional[str]`
- [x] Configurable max_length (default: 500)
- [x] Raises ValidationError on invalid input

### 1.4 Pattern Validation ✅
- [x] Write test: valid pattern "*.md"
- [x] Write test: valid pattern with path "docs/*.md"
- [x] Write test: reject traversal "../file"
- [x] Write test: reject absolute path "/file"
- [x] Write test: reject UNC path "\\\\server\\*.md"
- [x] Write test: reject __ in pattern
- [x] Implement `validate_pattern(pattern: str) -> str`
- [x] Uses `is_absolute_path()` helper
- [x] Raises ValidationError on invalid input

### 1.5 Result Handler Decorator ✅
- [x] Create `@validate_result` decorator in `mcp_core/result_handler.py`
- [x] Converts ValidationError to Result[T]
- [x] Preserves error_type and instruction
- [x] Optional message and success_instruction parameters
- [x] Write 8 tests covering all decorator functionality
- [x] 100% coverage on result_handler.py

### 1.6 Quality Checks ✅
- [x] Add docstrings to all functions
- [x] Run ruff format
- [x] Run ruff check
- [x] Run mypy
- [x] Update `mcp_core/__init__.py` exports

**Phase 1 Results:**
- ✅ 36 tests passing (28 validation + 8 result_handler)
- ✅ 100% coverage on validation.py (55 statements)
- ✅ 100% coverage on result_handler.py (22 statements)
- ✅ All quality checks pass
- ✅ 176 total tests passing, 88% overall coverage
- ✅ Ready for Phase 2

**Files Created:**
- `src/mcp_core/validation.py`
- `src/mcp_core/result_handler.py`
- `tests/unit/mcp_core/test_validation.py`
- `tests/unit/mcp_core/test_result_handler.py`

**Files Deleted:**
- `src/mcp_guide/tools/validation.py` (moved to mcp_core)
- `tests/unit/mcp_guide/tools/test_validation.py` (moved to mcp_core)

## Phase 2: category_list Tool ✅ COMPLETE

### 2.1 category_list - RED ✅
- [x] Write test: list empty categories
- [x] Write test: list single category
- [x] Write test: list multiple categories
- [x] Write test: no active session error
- [x] Write test: Result pattern response

### 2.2 category_list - GREEN ✅
- [x] Create `src/mcp_guide/tools/tool_category.py`
- [x] Define `CategoryListArgs(ToolArguments)` with verbose field
- [x] Implement `@ToolArguments.declare` decorated function
- [x] Get current session from active_sessions ContextVar
- [x] Get project config from session._cached_project
- [x] Format category list (name, dir, patterns, description)
- [x] Return Result.ok with list
- [x] All tests pass

### 2.3 category_list - REFACTOR ✅
- [x] Add comprehensive docstring with examples
- [x] Run ruff format
- [x] Run ruff check
- [x] Run mypy
- [x] Verify 95% coverage (only missing no_project error path)

**Phase 2 Results:**
- ✅ 5 tests passing
- ✅ 95% coverage on tool_category.py (20 statements, 1 miss)
- ✅ All quality checks pass
- ✅ Ready for Phase 3

**Files Created:**
- `src/mcp_guide/tools/tool_category.py`
- `tests/unit/mcp_guide/tools/test_tool_category.py`

## Phase 3: category_add Tool

### 3.1 category_add - RED
- [ ] Write test: add category with minimal args
- [ ] Write test: add category with all args
- [ ] Write test: reject duplicate name
- [ ] Write test: reject invalid name
- [ ] Write test: reject invalid directory
- [ ] Write test: reject invalid description
- [ ] Write test: reject invalid patterns
- [ ] Write test: auto-save after add
- [ ] Write test: no active session error

### 3.2 category_add - GREEN
- [ ] Define `CategoryAddArgs(ToolArguments)`
- [ ] Implement `category_add` function
- [ ] Get current session
- [ ] Validate all inputs using validation functions
- [ ] Check category doesn't exist
- [ ] Create new category
- [ ] Add to project config
- [ ] **Auto-save config immediately**
- [ ] Return Result.ok
- [ ] All tests pass

### 3.3 category_add - REFACTOR
- [ ] Add comprehensive docstring with examples
- [ ] Run ruff format
- [ ] Run mypy
- [ ] Verify >80% coverage

## Phase 4: category_remove Tool

### 4.1 category_remove - RED
- [ ] Write test: remove existing category
- [ ] Write test: reject non-existent category
- [ ] Write test: auto-remove from collections
- [ ] Write test: auto-save after remove
- [ ] Write test: no active session error

### 4.2 category_remove - GREEN
- [ ] Define `CategoryRemoveArgs(ToolArguments)`
- [ ] Implement `category_remove` function
- [ ] Get current session
- [ ] Validate category exists
- [ ] Remove from all collections
- [ ] Remove from project config
- [ ] **Auto-save config immediately**
- [ ] Return Result.ok
- [ ] All tests pass

### 4.3 category_remove - REFACTOR
- [ ] Add comprehensive docstring
- [ ] Run ruff format
- [ ] Run mypy
- [ ] Verify >80% coverage

## Phase 5: category_change Tool

### 5.1 category_change - RED
- [ ] Write test: rename category
- [ ] Write test: change directory
- [ ] Write test: change description
- [ ] Write test: replace patterns
- [ ] Write test: clear description with empty string
- [ ] Write test: reject new_name conflict
- [ ] Write test: update collections on rename
- [ ] Write test: auto-save after change
- [ ] Write test: reject non-existent category
- [ ] Write test: validate all new values

### 5.2 category_change - GREEN
- [ ] Define `CategoryChangeArgs(ToolArguments)`
- [ ] Implement `category_change` function
- [ ] Get current session
- [ ] Validate category exists
- [ ] Validate new_name if provided
- [ ] Validate all new values
- [ ] Replace category configuration
- [ ] Update collections if renamed
- [ ] **Auto-save config immediately**
- [ ] Return Result.ok
- [ ] All tests pass

### 5.3 category_change - REFACTOR
- [ ] Add comprehensive docstring
- [ ] Run ruff format
- [ ] Run mypy
- [ ] Verify >80% coverage

## Phase 6: category_update Tool

### 6.1 category_update - RED
- [ ] Write test: add patterns
- [ ] Write test: remove patterns
- [ ] Write test: add and remove patterns (remove first)
- [ ] Write test: ignore non-existent pattern removal (idempotent)
- [ ] Write test: auto-save after update
- [ ] Write test: reject non-existent category
- [ ] Write test: validate added patterns

### 6.2 category_update - GREEN
- [ ] Define `CategoryUpdateArgs(ToolArguments)`
- [ ] Implement `category_update` function
- [ ] Get current session
- [ ] Validate category exists
- [ ] Remove patterns if specified
- [ ] Add patterns if specified
- [ ] Validate new patterns
- [ ] **Auto-save config immediately**
- [ ] Return Result.ok
- [ ] All tests pass

### 6.3 category_update - REFACTOR
- [ ] Add comprehensive docstring
- [ ] Run ruff format
- [ ] Run mypy
- [ ] Verify >80% coverage

## Phase 7: Configuration Persistence Helper

### 7.1 Auto-Save Helper - RED
- [ ] Write test: successful save
- [ ] Write test: file locking
- [ ] Write test: validation before write
- [ ] Write test: write error handling
- [ ] Write test: concurrent access

### 7.2 Auto-Save Helper - GREEN
- [ ] Implement `_save_project_config(session, project) -> Result[None]`
- [ ] Use existing file_lock module
- [ ] Validate project before write
- [ ] Write to disk
- [ ] Handle errors gracefully
- [ ] All tests pass

### 7.3 Auto-Save Helper - REFACTOR
- [ ] Add docstrings
- [ ] Run ruff format
- [ ] Run mypy

## Phase 8: Integration Testing

### 8.1 Integration Tests
- [ ] Test full workflow: list → add → list → change → list → remove → list
- [ ] Test collection auto-update on category remove
- [ ] Test collection auto-update on category rename
- [ ] Test concurrent access with multiple sessions
- [ ] Test error recovery
- [ ] All integration tests pass

## Phase 9: Documentation

### 9.1 Tool Documentation
- [ ] Create `docs/tools/category-tools.md`
- [ ] Document each tool with examples
- [ ] Document validation rules
- [ ] Document auto-save behavior
- [ ] Document error types and handling

### 9.2 Update README
- [ ] Add category tools section
- [ ] Link to tool documentation

## Phase 10: Final Checks

### 10.1 Quality Checks
- [ ] Run full test suite - 100% pass
- [ ] Run ruff check - no warnings
- [ ] Run mypy - no errors
- [ ] Verify >80% coverage for all new code
- [ ] Run ruff format - all formatted

### 10.2 Verification
- [ ] All spec requirements met
- [ ] All acceptance criteria met
- [ ] Auto-save works on every change
- [ ] No breaking changes
- [ ] Ready for production

## Key Implementation Notes

### Auto-Save Pattern
Every tool MUST follow this pattern:
```python
# 1. Validate inputs
# 2. Modify project config
# 3. Save immediately
result = await _save_project_config(session, updated_project)
if not result.success:
    return result.to_json()
# 4. Return success only after save
return Result.ok(data).to_json()
```

### Collection Auto-Update
When category is removed or renamed:
1. Iterate through all collections
2. Update/remove category references
3. Save updated project (single save for all changes)

### Validation Order
1. Session exists
2. Input validation (names, paths, patterns)
3. Business logic validation (exists, doesn't exist, conflicts)
4. Modification
5. Auto-save
6. Return success

### Error Handling
- Use Result pattern for all returns
- Provide specific error_type for each failure
- Include instruction field for agent guidance
- Never return success without successful save

## Success Criteria

- [ ] All 5 tools implemented and tested
- [ ] All validation functions working
- [ ] Auto-save on every change
- [ ] Collection auto-update working
- [ ] >80% test coverage
- [ ] All quality checks pass
- [ ] Documentation complete
- [ ] Ready for production use
