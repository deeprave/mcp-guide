# Frontmatter Instruction Handling Tasks

## Task 1: Fix Content-Size Implementation Gap ✅
**File**: `src/mcp_guide/utils/content_formatter_mime.py`
**Priority**: High
**Status**: COMPLETED

- [x] Updated MIME formatter to use `file_info.content_size` instead of calculating `len(content.encode("utf-8"))`
- [x] Fixed both `format_single` and `format_multiple` methods
- [x] Ensured accurate HTTP Content-Length headers

## Task 2: Add Content-Size Test Coverage ✅
**Files**: Various test files
**Priority**: High
**Status**: COMPLETED

- [x] Added `test_format_single_uses_content_size_not_content_length` test
- [x] Added `test_format_multiple_uses_content_size` test
- [x] Created comprehensive integration tests in `test_content_size_mime_integration.py`
- [x] Added 4 integration test scenarios verifying content_size usage
- [x] Verified Content-Length headers reflect content size after frontmatter removal

## Task 3: Code Quality Validation ✅
**Status**: COMPLETED

- [x] All 1072 tests passing
- [x] Ruff check passed (all checks passed)
- [x] MyPy validation passed (no issues found in 85 source files)
- [x] Code formatting validated (all files properly formatted)

## Task 4: Extend Frontmatter Utilities ✅
**File**: `src/mcp_guide/utils/frontmatter.py`
**Priority**: High
**Status**: COMPLETED

Add new functions following existing patterns:
- [x] Add `get_frontmatter_instruction()` function (similar to `get_frontmatter_description()`)
- [x] Add `get_frontmatter_type()` function
- [x] Add `get_frontmatter_partials()` function (basic parsing for future use) - **✅ IMPLEMENTED**
- [x] Add `get_type_based_default_instruction()` function
- [x] Add content type constants (`USER_INFO`, `AGENT_INFO`, `AGENT_INSTRUCTION`)
- [x] Add `validate_content_type()` function with logging for invalid types

## Task 5: Update Content Processing ✅
**File**: `src/mcp_guide/utils/content_common.py`
**Priority**: High
**Status**: COMPLETED

Update content processing to handle frontmatter:
- [x] Update `read_and_render_file_contents()` to use `parse_frontmatter_content()`
- [x] Strip frontmatter from content output
- [x] Add instruction extraction and deduplication logic
- [x] Handle multiple document instruction merging

## Task 6: Update Content Formatters ✅
**Files**: `src/mcp_guide/utils/content_formatter_*.py`
**Priority**: Medium
**Status**: COMPLETED

Enhance formatters to process frontmatter:
- [x] Fixed content_size usage in MIME formatter (completed as part of Task 1)
- [x] Fixed Content-Length calculation to use final rendered content (per code review)
- [x] Strip frontmatter from content output in both formatters
- [x] Extract and process frontmatter metadata
- [x] Apply type-based instruction logic

## Task 7: Update Get Content Tool ✅
**File**: `src/mcp_guide/tools/tool_content.py`
**Priority**: High
**Status**: COMPLETED

Integrate frontmatter processing:
- [x] Use extracted instructions from frontmatter
- [x] Apply type-based result construction
- [x] Handle instruction deduplication

## Task 8: Update Category Content Tool ✅
**File**: `src/mcp_guide/tools/tool_category.py`
**Priority**: High
**Status**: COMPLETED

Apply frontmatter processing to category content:
- [x] Use same frontmatter processing logic as get_content
- [x] Ensure consistent behavior across content tools

## Task 9: Unit Tests for Frontmatter Processing ✅
**Files**: Various test files
**Priority**: High
**Status**: COMPLETED

Comprehensive test coverage:
- [x] Test frontmatter instruction extraction
- [x] Test content type validation
- [x] Test instruction deduplication
- [x] Test content stripping
- [x] Test type-based behavior for all content types
- [x] Added edge case tests (no frontmatter, malformed YAML, unterminated frontmatter)
- [x] Updated tests to reflect corrected Content-Length behavior (using final rendered content)

## Task 10: Integration Tests for Frontmatter Processing ✅
**File**: `tests/integration/test_frontmatter_processing.py` (new)
**Priority**: Medium
**Status**: COMPLETED

End-to-end testing:
- [x] Test `@guide checks` command behavior
- [x] Test mixed content type handling
- [x] Test backward compatibility with content without frontmatter
