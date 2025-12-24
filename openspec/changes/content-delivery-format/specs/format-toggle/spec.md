# Content Delivery Format Specification

## Overview

This specification defines how content delivery format selection works using the `content-format-mime` feature flag.

## Feature Flag Definition

### Flag Name
`content-format-mime`

### Flag Type
Boolean

### Flag Behavior
- **`false` or absent**: Use plain text format (default)
- **`true`**: Use MIME-multipart format

### Flag Scope
- **Global**: Can be set as global feature flag
- **Project**: Can be overridden at project level
- **Resolution**: Project flag takes precedence over global flag

## Format Selection Logic

### Default Behavior
```
IF content-format-mime flag is absent OR false
THEN use PlainFormatter
ELSE use MimeFormatter
```

### Flag Resolution Order
1. **Project flag**: Check project-specific `content-format-mime` setting
2. **Global flag**: Check global `content-format-mime` setting
3. **Default**: Use plain format if no flags set

## Implementation Requirements

### Formatter Selection
- **Location**: `src/mcp_guide/utils/formatter_selection.py`
- **Function**: `get_active_formatter()`
- **Logic**: Check feature flag and return appropriate formatter instance

### Feature Flag Integration
- **Use existing**: Leverage current feature flag system
- **Flag validation**: Ensure boolean type validation
- **Flag resolution**: Use existing project/global resolution logic

### Content Tool Integration
- **Tools affected**: All content delivery tools (get_content, category_content)
- **Integration point**: Use formatter selection utility
- **Backward compatibility**: Maintain existing API

## Format Specifications

### Plain Format
- **Current behavior**: Concatenated text with file separators
- **Use case**: Simple text output, terminal display
- **Structure**: File headers + content blocks

### MIME-multipart Format
- **Structure**: RFC-compliant multipart format with boundaries
- **Use case**: Structured output, external tool integration
- **Headers**: Content-Type, Content-Disposition per part

## Configuration Examples

### Global Flag Setting
```bash
# Enable MIME format globally
mcp-guide set-feature-flag content-format-mime true

# Disable MIME format (use plain)
mcp-guide set-feature-flag content-format-mime false
```

### Project Flag Setting
```bash
# Enable MIME format for current project
mcp-guide set-project-flag content-format-mime true

# Use global setting for current project
mcp-guide set-project-flag content-format-mime null
```

## Backward Compatibility

### Default Behavior
- **No change**: Plain format remains default
- **Existing tools**: Continue working without modification
- **Flag absence**: Treated as false (plain format)

### Migration Path
- **Opt-in**: Users must explicitly enable MIME format
- **Gradual adoption**: Can test MIME format per project
- **Rollback**: Can disable flag to return to plain format
