# Implementation Plan: Content Delivery Format Toggle

## Phase 1: Feature Flag Integration

### 1.1 Update Formatter Selection Logic
- **File**: `src/mcp_guide/utils/formatter_selection.py`
- **Changes**:
  - Add `get_formatter_from_flag()` function
  - Integrate with feature flag resolution system
  - Update `get_active_formatter()` to check flags

### 1.2 Feature Flag Validation
- **File**: `src/mcp_guide/feature_flags/validation.py`
- **Changes**:
  - Add `content-format-mime` to valid flag names
  - Ensure boolean type validation

## Phase 2: Content Tool Integration

### 2.1 Update Get Content Tool
- **File**: `src/mcp_guide/tools/tool_content.py`
- **Changes**:
  - Use flag-based formatter selection
  - Remove hardcoded formatter choice
  - Maintain existing API

### 2.2 Update Category Content Tool
- **File**: `src/mcp_guide/tools/tool_category.py` (category_content function)
- **Changes**:
  - Use flag-based formatter selection
  - Ensure consistent behavior with get_content

## Phase 3: Testing and Validation

### 3.1 Unit Tests
- **File**: `tests/unit/test_mcp_guide/utils/test_formatter_selection.py`
- **Tests**:
  - Test flag-based formatter selection
  - Test flag resolution (project > global > default)
  - Test boolean flag validation

### 3.2 Integration Tests
- **File**: `tests/integration/test_content_format_flag.py` (new)
- **Tests**:
  - Test global flag setting and content output
  - Test project flag override
  - Test default behavior (plain format)

### 3.3 Feature Flag Tests
- **File**: `tests/unit/test_feature_flag_implementations.py`
- **Tests**:
  - Test `content-format-mime` flag behavior
  - Test flag resolution with project/global settings

## Implementation Details

### Formatter Selection Logic
```python
def get_formatter_from_flag() -> ContentFormatter:
    """Get formatter based on content-format-mime flag."""
    # Check project flag first, then global, then default
    mime_enabled = resolve_flag("content-format-mime", default=False)

    if mime_enabled:
        return MimeFormatter()
    else:
        return PlainFormatter()
```

### Flag Resolution Integration
```python
from mcp_guide.feature_flags.resolution import resolve_flag

def get_active_formatter() -> ContentFormatter:
    """Get active formatter based on feature flags."""
    return get_formatter_from_flag()
```

### Content Tool Updates
```python
# In tool_content.py and tool_category.py
from mcp_guide.utils.formatter_selection import get_active_formatter

# Replace hardcoded formatter with:
formatter = get_active_formatter()
```

## Testing Strategy

### Flag Behavior Tests
- Test flag absent (default to plain)
- Test flag false (use plain)
- Test flag true (use MIME)
- Test invalid flag values

### Resolution Tests
- Test project flag overrides global flag
- Test global flag when no project flag
- Test default when no flags set

### Integration Tests
- Test actual content output format
- Test tool behavior with different flag settings
- Test backward compatibility

## Implementation Order

1. **Feature Flag Integration** (Phase 1) - Core functionality
2. **Content Tool Integration** (Phase 2) - User-facing changes
3. **Testing and Validation** (Phase 3) - Quality assurance

## Backward Compatibility

### No Breaking Changes
- Default behavior unchanged (plain format)
- Existing tool APIs unchanged
- Flag absence treated as false

### Migration Support
- Users can gradually adopt MIME format
- Easy rollback by disabling flag
- Project-level testing before global adoption
