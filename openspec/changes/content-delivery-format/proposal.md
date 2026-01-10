# Content Delivery Format Selection

**Priority**: Medium
**Complexity**: Low

## Why

Currently, the content delivery format is hardcoded. Users need flexible content formatting options for different use cases:
- **Raw content stream**: For simple consumption without file boundaries
- **Structured plain format**: For readable multi-file output with separators
- **MIME-multipart format**: For structured integration with external tools

## What

Implement a feature flag system to allow users to select between content delivery formats:

- **Feature flag**: `content-format-mime` (string)
- **Format options**:
  - `None`/"none" (default): Raw content stream without file separators
  - `"plain"`: Plain text format with file separators and headers
  - `"mime"`: MIME-multipart format with boundaries and headers
- **Scope**: Project and global flags with project precedence

## How

1. **Replace ContextVar system**: Remove existing ContextVar-based formatter selection
2. **Feature flag integration**: Use string-based `content-format-mime` flag
3. **Format enum**: Create ContentFormat enum for type safety
4. **BaseFormatter**: Add new formatter for raw content stream (default)
5. **Flag validators**: Add validation for content format and template styling flags
6. **Project-level support**: Respect project-specific flag settings

## Success Criteria

- Users can set `content-format-mime` flag to select format (none/plain/mime)
- Default behavior provides raw content stream without separators
- Content tools respect flag settings with project override capability
- Feature flag validation prevents invalid format values
