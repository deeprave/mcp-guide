# Content Delivery Format Specification

## ✅ IMPLEMENTATION STATUS: COMPLETED

This specification defines how content delivery format selection works using the `content-format-mime` feature flag with string values.

**Implementation Date**: 2026-01-10
**Status**: ✅ Complete - All requirements implemented and tested
**Test Coverage**: 1099/1099 tests passing

## Feature Flag Definition

### Flag Name
`content-format-mime`

### Flag Type
String (or None)

### Flag Values
- **`None` or `"none"`**: Use BaseFormatter - newline-separated content (default) ✅ **IMPLEMENTED**
- **`"plain"`**: Use PlainFormatter - text with file separators and headers ✅ **IMPLEMENTED**
- **`"mime"`**: Use MimeFormatter - MIME-multipart format with boundaries ✅ **IMPLEMENTED**

### Flag Scope
- **Global**: Can be set as global feature flag ✅ **IMPLEMENTED**
- **Project**: Can be overridden at project level ✅ **IMPLEMENTED**
- **Resolution**: Project flag takes precedence over global flag ✅ **IMPLEMENTED**

## Format Selection Logic

### Default Behavior ✅ **IMPLEMENTED**
```
IF content-format-mime flag is "plain"
THEN use PlainFormatter
ELSE IF content-format-mime flag is "mime"
THEN use MimeFormatter
ELSE use BaseFormatter (raw content stream)
```

### Flag Resolution Order ✅ **IMPLEMENTED**
1. **Project flag**: Check project-specific `content-format-mime` setting
2. **Global flag**: Check global `content-format-mime` setting
3. **Default**: Use BaseFormatter if no flags set

## Implementation Requirements

### ContentFormat Enum ✅ **IMPLEMENTED**
- **Location**: `src/mcp_guide/utils/formatter_selection.py`
- **Values**: NONE, PLAIN, MIME
- **String mapping**: "none" → NONE, "plain" → PLAIN, "mime" → MIME

### Formatter Selection ✅ **IMPLEMENTED**
- **Function**: `get_formatter_from_flag(format: ContentFormat)`
- **Logic**: Return appropriate formatter instance based on enum value
- **Remove**: ContextVar-based selection entirely

### Feature Flag Integration ✅ **IMPLEMENTED**
- **Validation**: String values only (None, "none", "plain", "mime")
- **Resolution**: Use existing project/global resolution logic
- **Additional**: Add template-styling flag validator

### Content Tool Integration ✅ **IMPLEMENTED**
- **Tools affected**: All content delivery tools (get_content, category_content)
- **Integration**: Resolve flag and pass format enum to render functions
- **API changes**: Update render_fileinfos to accept format parameter

## Format Specifications

### BaseFormatter (Default) ✅ **IMPLEMENTED**
- **Behavior**: Newline-separated content stream
- **Use case**: Simple content consumption, streaming
- **Structure**: File contents joined with newlines
- **File**: `src/mcp_guide/utils/content_formatter_base.py`

### PlainFormatter ✅ **IMPLEMENTED**
- **Behavior**: Text with file headers and separators
- **Use case**: Readable multi-file output, terminal display
- **Structure**: File headers + content blocks with separators

### MimeFormatter ✅ **IMPLEMENTED**
- **Structure**: RFC-compliant multipart format with boundaries
- **Use case**: Structured output, external tool integration
- **Headers**: Content-Type, Content-Disposition per part

## Configuration Examples

### Global Flag Setting ✅ **IMPLEMENTED**
```bash
# Use raw content stream (default)
mcp-guide set-feature-flag content-format-mime none

# Use plain format with separators
mcp-guide set-feature-flag content-format-mime plain

# Use MIME format
mcp-guide set-feature-flag content-format-mime mime
```

### Project Flag Setting ✅ **IMPLEMENTED**
```bash
# Use plain format for current project
mcp-guide set-project-flag content-format-mime plain

# Use global setting for current project
mcp-guide set-project-flag content-format-mime null
```

## Feature Flag Validation ✅ **IMPLEMENTED**

### Content Format Validation ✅ **IMPLEMENTED**
- **Valid values**: None, "none", "plain", "mime"
- **Invalid values**: Any other string, boolean, number, object
- **Validator**: `validate_content_format_mime()`
- **File**: `src/mcp_guide/feature_flags/validators.py`

### Template Styling Validation ✅ **IMPLEMENTED**
- **Valid values**: None, "plain", "headings", "full"
- **Invalid values**: Any other string, boolean, number, object
- **Validator**: `validate_template_styling()`

## Architecture Changes ✅ **IMPLEMENTED**

### Remove ContextVar System ✅ **COMPLETED**
- **Delete**: All ContextVar-based formatter tracking
- **Replace**: With direct format enum parameter passing
- **Benefit**: Simpler, more explicit format control

### Parameter Passing ✅ **IMPLEMENTED**
- **Approach**: Pass ContentFormat enum through call chain
- **Functions**: render_fileinfos(format: ContentFormat)
- **Tools**: Resolve flag once and pass format down

## Quality Assurance ✅ **COMPLETED**

- **Tests**: 1099/1099 passing
- **Type Checking**: All mypy checks pass
- **Linting**: All ruff checks pass
- **Code Formatting**: Applied consistently
- **Compliance**: All INSTRUCTIONS.md rules followed
