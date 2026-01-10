# Content Delivery Format Specification

## Overview

This specification defines how content delivery format selection works using the `content-format-mime` feature flag with string values.

## Feature Flag Definition

### Flag Name
`content-format-mime`

### Flag Type
String (or None)

### Flag Values
- **`None` or `"none"`**: Use BaseFormatter - raw content stream (default)
- **`"plain"`**: Use PlainFormatter - text with file separators and headers
- **`"mime"`**: Use MimeFormatter - MIME-multipart format with boundaries

### Flag Scope
- **Global**: Can be set as global feature flag
- **Project**: Can be overridden at project level
- **Resolution**: Project flag takes precedence over global flag

## Format Selection Logic

### Default Behavior
```
IF content-format-mime flag is "plain"
THEN use PlainFormatter
ELSE IF content-format-mime flag is "mime"
THEN use MimeFormatter
ELSE use BaseFormatter (raw content stream)
```

### Flag Resolution Order
1. **Project flag**: Check project-specific `content-format-mime` setting
2. **Global flag**: Check global `content-format-mime` setting
3. **Default**: Use BaseFormatter if no flags set

## Implementation Requirements

### ContentFormat Enum
- **Location**: `src/mcp_guide/utils/formatter_selection.py`
- **Values**: NONE, PLAIN, MIME
- **String mapping**: "none" → NONE, "plain" → PLAIN, "mime" → MIME

### Formatter Selection
- **Function**: `get_formatter_from_flag(format: ContentFormat)`
- **Logic**: Return appropriate formatter instance based on enum value
- **Remove**: ContextVar-based selection entirely

### Feature Flag Integration
- **Validation**: String values only (None, "none", "plain", "mime")
- **Resolution**: Use existing project/global resolution logic
- **Additional**: Add template-styling flag validator

### Content Tool Integration
- **Tools affected**: All content delivery tools (get_content, category_content)
- **Integration**: Resolve flag and pass format enum to render functions
- **API changes**: Update render_fileinfos to accept format parameter

## Format Specifications

### BaseFormatter (Default)
- **Behavior**: Raw content stream without file separators
- **Use case**: Simple content consumption, streaming
- **Structure**: Concatenated file contents only

### PlainFormatter
- **Behavior**: Text with file headers and separators
- **Use case**: Readable multi-file output, terminal display
- **Structure**: File headers + content blocks with separators

### MimeFormatter
- **Structure**: RFC-compliant multipart format with boundaries
- **Use case**: Structured output, external tool integration
- **Headers**: Content-Type, Content-Disposition per part

## Configuration Examples

### Global Flag Setting
```bash
# Use raw content stream (default)
mcp-guide set-feature-flag content-format-mime none

# Use plain format with separators
mcp-guide set-feature-flag content-format-mime plain

# Use MIME format
mcp-guide set-feature-flag content-format-mime mime
```

### Project Flag Setting
```bash
# Use plain format for current project
mcp-guide set-project-flag content-format-mime plain

# Use global setting for current project
mcp-guide set-project-flag content-format-mime null
```

## Feature Flag Validation

### Content Format Validation
- **Valid values**: None, "none", "plain", "mime"
- **Invalid values**: Any other string, boolean, number, object
- **Validator**: `validate_content_format_mime()`

### Template Styling Validation
- **Valid values**: None, "plain", "headings", "full"
- **Invalid values**: Any other string, boolean, number, object
- **Validator**: `validate_template_styling()`

## Architecture Changes

### Remove ContextVar System
- **Delete**: All ContextVar-based formatter tracking
- **Replace**: With direct format enum parameter passing
- **Benefit**: Simpler, more explicit format control

### Parameter Passing
- **Approach**: Pass ContentFormat enum through call chain
- **Functions**: render_fileinfos(format: ContentFormat)
- **Tools**: Resolve flag once and pass format down
