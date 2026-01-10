# Content Delivery Format Tasks

## Task 1: Create BaseFormatter and ContentFormat Enum
**File**: `src/mcp_guide/utils/content_formatter_base.py` (new)
**File**: `src/mcp_guide/utils/formatter_selection.py` (major update)
**Priority**: High
**Estimated Effort**: 2-3 hours

Create new formatter and enum system:
- [ ] Create `ContentFormat` enum (NONE, PLAIN, MIME)
- [ ] Create `BaseFormatter` class for raw content stream
- [ ] Remove all ContextVar-based logic from formatter_selection.py
- [ ] Add `get_formatter_from_flag(format: ContentFormat)` function
- [ ] Update type hints and imports

## Task 2: Add Feature Flag Validators
**File**: `src/mcp_guide/feature_flags/validators.py`
**Priority**: High
**Estimated Effort**: 1 hour

Add validation for new flags:
- [ ] Add `validate_content_format_mime()` function
- [ ] Add `validate_template_styling()` function
- [ ] Register both validators in module initialization
- [ ] Test validator functions with valid/invalid values

## Task 3: Update Content Common Function
**File**: `src/mcp_guide/utils/content_common.py`
**Priority**: High
**Estimated Effort**: 1 hour

Update render function signature:
- [ ] Add `format: ContentFormat` parameter to `render_fileinfos()`
- [ ] Pass format to `get_formatter_from_flag()` instead of using ContextVar
- [ ] Update all callers to pass format parameter
- [ ] Remove any ContextVar imports

## Task 4: Update Get Content Tool
**File**: `src/mcp_guide/tools/tool_content.py`
**Priority**: High
**Estimated Effort**: 1-2 hours

Add flag resolution:
- [ ] Import ContentFormat enum and resolution functions
- [ ] Resolve `content-format-mime` flag from session
- [ ] Convert flag value to ContentFormat enum
- [ ] Pass format to `render_fileinfos()` calls
- [ ] Handle flag resolution errors

## Task 5: Update Category Content Tool
**File**: `src/mcp_guide/tools/tool_category.py`
**Priority**: High
**Estimated Effort**: 1-2 hours

Add flag resolution to category_content:
- [ ] Import ContentFormat enum and resolution functions
- [ ] Resolve `content-format-mime` flag from session
- [ ] Convert flag value to ContentFormat enum
- [ ] Pass format to `render_fileinfos()` calls
- [ ] Handle flag resolution errors

## Task 6: Unit Tests for BaseFormatter
**File**: `tests/unit/test_mcp_guide/utils/test_content_formatter_base.py` (new)
**Priority**: High
**Estimated Effort**: 1-2 hours

Test new BaseFormatter:
- [ ] Test format method with empty file list
- [ ] Test format method with single file
- [ ] Test format method with multiple files
- [ ] Test content concatenation without separators
- [ ] Test handling of None content

## Task 7: Update Formatter Selection Tests
**File**: `tests/unit/test_mcp_guide/utils/test_formatter_selection.py`
**Priority**: High
**Estimated Effort**: 2-3 hours

Test new enum-based system:
- [ ] Remove all ContextVar-related tests
- [ ] Test ContentFormat enum values and string mapping
- [ ] Test `get_formatter_from_flag()` with each format type
- [ ] Test formatter instance types returned
- [ ] Test invalid format handling

## Task 8: Feature Flag Validation Tests
**File**: `tests/unit/test_feature_flag_validation.py`
**Priority**: Medium
**Estimated Effort**: 1-2 hours

Test new validators:
- [ ] Test `content-format-mime` validator with valid values
- [ ] Test `content-format-mime` validator with invalid values
- [ ] Test `template-styling` validator with valid values
- [ ] Test `template-styling` validator with invalid values
- [ ] Test validator registration

## Task 9: Integration Tests for Content Tools
**File**: `tests/integration/test_content_format_flag.py` (new)
**Priority**: Medium
**Estimated Effort**: 2-3 hours

Test end-to-end behavior:
- [ ] Test global flag setting affects content output format
- [ ] Test project flag override functionality
- [ ] Test default behavior (BaseFormatter/raw content)
- [ ] Test actual output format differences between formatters
- [ ] Test flag resolution error handling

## Task 10: Update Content Common Tests
**File**: `tests/unit/test_mcp_guide/utils/test_content_common.py`
**Priority**: Medium
**Estimated Effort**: 1 hour

Update tests for new signature:
- [ ] Update `render_fileinfos()` test calls to include format parameter
- [ ] Test format parameter passing to formatter
- [ ] Remove any ContextVar-related test setup
