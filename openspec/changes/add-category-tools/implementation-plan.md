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

## Phase 3: category_add Tool ✅ COMPLETE

### 3.1 category_add - RED ✅
- [x] Write test: add category with minimal args
- [x] Write test: add category with all args
- [x] Write test: add category with multiple patterns
- [x] Write test: reject duplicate name
- [x] Write test: reject invalid name
- [x] Write test: reject invalid directory
- [x] Write test: reject invalid description
- [x] Write test: reject invalid patterns
- [x] Write test: auto-save after add
- [x] Write test: no active session error
- [x] Write test: save failure handling

### 3.2 category_add - GREEN ✅
- [x] Define `CategoryAddArgs(ToolArguments)`
- [x] Implement `category_add` function
- [x] Get current session
- [x] Validate all inputs using validation functions
- [x] Check category doesn't exist
- [x] Create new category
- [x] Add to project config
- [x] **Auto-save config immediately**
- [x] Return Result.ok
- [x] All tests pass

### 3.3 category_add - REFACTOR ✅
- [x] Add comprehensive docstring with examples
- [x] Run ruff format
- [x] Run ruff check
- [x] Run mypy
- [x] Verify >80% coverage (94% achieved)

**Phase 3 Results:**
- ✅ 18 new tests passing (all category_add tests + timestamp + length validation)
- ✅ 246 total tests passing, 87% overall coverage
- ✅ 93% coverage on tool_category.py
- ✅ All quality checks pass
- ✅ Immutability pattern correctly implemented using `session.update_config()` and `Project.with_category()`
- ✅ Timestamp test verifies immutability contract is honored
- ✅ DRY principle honored - validation delegated to Category model
- ✅ Ready for Phase 4

**Files Modified:**
- `src/mcp_guide/tools/tool_category.py` - Added CategoryAddArgs and category_add
- `tests/unit/mcp_guide/tools/test_tool_category.py` - Added 18 tests for category_add

**Implementation Notes:**
- Uses `session.update_config(lambda p: p.with_category(category))` to maintain immutability
- Honors Project dataclass frozen contract
- Ensures `updated_at` timestamp is correctly set
- Cache management handled by Session.update_config
- Test `test_category_add_updates_timestamp` verifies immutability pattern works correctly
- Validation delegated to Category model (DRY) - catches ValueError and converts to ArgValidationError
- Test `test_category_add_invalid_name_too_long` verifies 30-character limit enforcement

## Phase 4: category_remove Tool ✅ COMPLETE

### 4.1 category_remove - RED ✅
- [x] Write test: remove existing category
- [x] Write test: reject non-existent category
- [x] Write test: auto-remove from single collection
- [x] Write test: auto-remove from multiple collections
- [x] Write test: category not in collections
- [x] Write test: auto-save after remove
- [x] Write test: no active session error
- [x] Write test: save failure handling
- [x] Write test: updates timestamp

### 4.2 category_remove - GREEN ✅
- [x] Define `CategoryRemoveArgs(ToolArguments)`
- [x] Implement `category_remove` function
- [x] Get current session
- [x] Validate category exists
- [x] Remove from all collections using list comprehension
- [x] Remove from project config using `Project.without_category()`
- [x] **Auto-save config immediately**
- [x] Return Result.ok
- [x] All tests pass

### 4.3 category_remove - REFACTOR ✅
- [x] Add comprehensive docstring
- [x] Run ruff format
- [x] Run ruff check
- [x] Run mypy
- [x] Verify >90% coverage (95% achieved)

**Phase 4 Results:**
- ✅ 9 tests passing
- ✅ 95% coverage on tool_category.py
- ✅ All quality checks pass
- ✅ Collections automatically updated when category removed
- ✅ Immutability pattern maintained
- ✅ Ready for Phase 5

**Files Modified:**
- `src/mcp_guide/tools/tool_category.py` - Added CategoryRemoveArgs and category_remove
- `tests/unit/mcp_guide/tools/test_tool_category.py` - Added 9 tests for category_remove

## Phase 5: category_change Tool ✅ COMPLETE

### 5.1 category_change - RED ✅
- [x] Write test: rename category
- [x] Write test: change directory
- [x] Write test: change description
- [x] Write test: replace patterns
- [x] Write test: clear description with empty string
- [x] Write test: change multiple fields
- [x] Write test: rename updates single collection
- [x] Write test: rename updates multiple collections
- [x] Write test: reject non-existent category
- [x] Write test: reject new_name conflict
- [x] Write test: validate invalid new_name
- [x] Write test: validate invalid new_dir
- [x] Write test: validate invalid new_description
- [x] Write test: validate invalid new_pattern
- [x] Write test: reject no changes provided
- [x] Write test: auto-save after change
- [x] Write test: no active session error
- [x] Write test: save failure handling
- [x] Write test: updates timestamp
- [x] Write test: rename to same name (edge case added in CHECK phase)

### 5.2 category_change - GREEN ✅
- [x] Define `CategoryChangeArgs(ToolArguments)`
- [x] Implement `category_change` function
- [x] Get current session
- [x] Validate category exists
- [x] Validate at least one change provided
- [x] Validate new_name if provided (no conflict, valid format)
- [x] Validate new_dir if provided
- [x] Validate new_description if provided (empty string clears)
- [x] Validate new_patterns if provided
- [x] Build updated category with new values
- [x] Replace category in project
- [x] Update collections if renamed (optimized: only when name actually changes)
- [x] **Auto-save config immediately**
- [x] Return appropriate success message
- [x] All tests pass

### 5.3 category_change - REFACTOR ✅
- [x] Add comprehensive docstring with examples
- [x] Run ruff format
- [x] Run ruff check
- [x] Run mypy
- [x] Verify >90% coverage (97% achieved)
- [x] Refactor exception handling for consistency (CHECK phase)
- [x] Improve code clarity for description handling (CHECK phase)

**Phase 5 Results:**
- ✅ 20 tests passing (19 initial + 1 edge case)
- ✅ 97% coverage on tool_category.py (136 statements, 4 uncovered)
- ✅ All quality checks pass
- ✅ Collections automatically updated when category renamed
- ✅ Optimized: skips collection updates when name unchanged
- ✅ Empty string clears description (sets to None)
- ✅ Comprehensive validation and error handling
- ✅ Bug fix: Category descriptions now properly saved to config
- ✅ Ready for Phase 6

**Phase 5 CHECK Phase Improvements:**
- Exception handling refactored to match category_add pattern
- Added edge case test for same-name rename
- Improved code clarity with explicit description handling logic

**Files Modified:**
- `src/mcp_guide/tools/tool_category.py` - Added CategoryChangeArgs and category_change
- `src/mcp_guide/config.py` - Fixed _project_to_dict to include description field
- `tests/unit/mcp_guide/tools/test_tool_category.py` - Added 20 tests for category_change
- `.todo/phase5-category-change-tdd-plan.md` - Detailed TDD plan and completion status

**Critical Bug Fixed:**
- ConfigManager._project_to_dict() was not serializing category descriptions
- This affected all category operations, not just category_change
- Fix: Added "description": c.description to category serialization
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
