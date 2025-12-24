# Content Delivery Format Tasks

## Task 1: Update Formatter Selection Logic
**File**: `src/mcp_guide/utils/formatter_selection.py`
**Priority**: High
**Estimated Effort**: 1-2 hours

Implement flag-based formatter selection:
- Add `get_formatter_from_flag()` function
- Integrate with feature flag resolution system
- Update `get_active_formatter()` to check `content-format-mime` flag
- Use project flag > global flag > default (plain) resolution order

## Task 2: Feature Flag Validation
**File**: `src/mcp_guide/feature_flags/validation.py`
**Priority**: Medium
**Estimated Effort**: 30 minutes

Add validation for new flag:
- Add `content-format-mime` to valid flag names
- Ensure boolean type validation
- Test flag validation with valid/invalid values

## Task 3: Update Get Content Tool
**File**: `src/mcp_guide/tools/tool_content.py`
**Priority**: High
**Estimated Effort**: 30 minutes

Replace hardcoded formatter:
- Use `get_active_formatter()` instead of hardcoded selection
- Remove any direct formatter instantiation
- Maintain existing tool API

## Task 4: Update Category Content Tool
**File**: `src/mcp_guide/tools/tool_category.py`
**Priority**: High
**Estimated Effort**: 30 minutes

Update category_content function:
- Use `get_active_formatter()` for consistent behavior
- Ensure same flag-based selection as get_content tool
- Maintain existing functionality

## Task 5: Unit Tests for Formatter Selection
**File**: `tests/unit/test_mcp_guide/utils/test_formatter_selection.py`
**Priority**: High
**Estimated Effort**: 1-2 hours

Test flag-based formatter selection:
- Test flag absent (default to plain)
- Test flag false (use plain)
- Test flag true (use MIME)
- Test project flag overrides global flag
- Test invalid flag values

## Task 6: Integration Tests
**File**: `tests/integration/test_content_format_flag.py` (new)
**Priority**: Medium
**Estimated Effort**: 2-3 hours

Test end-to-end behavior:
- Test global flag setting affects content output
- Test project flag override functionality
- Test default behavior maintains backward compatibility
- Test actual output format differences

## Task 7: Feature Flag Implementation Tests
**File**: `tests/unit/test_feature_flag_implementations.py`
**Priority**: Medium
**Estimated Effort**: 1 hour

Test flag resolution:
- Test `content-format-mime` flag behavior
- Test flag resolution with project/global settings
- Test boolean validation
