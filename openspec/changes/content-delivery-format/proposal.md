# Content Delivery Format Toggle

**Priority**: Medium
**Complexity**: Low

## Why

Currently, the content delivery format is hardcoded to use plain text format. Users have no way to switch to the available MIME-multipart format, which provides better structure for multiple files and integration with external tools.

The system already supports both formats:
- **Plain format**: Simple concatenated text output
- **MIME-multipart format**: Structured format with boundaries and headers

However, there's no user-configurable way to choose between them.

## What

Implement a feature flag system to allow users to toggle between content delivery formats:

- **Feature flag**: `content-format-mime` (boolean)
- **Default behavior**: Plain format (flag absent or false)
- **Enabled behavior**: MIME-multipart format (flag set to true)
- **Scope**: Global flag that affects all content delivery

## How

1. **Feature flag integration**: Use existing feature flag system with `content-format-mime` flag
2. **Format selection logic**: Check flag value to determine which formatter to use
3. **Backward compatibility**: Default to plain format to maintain existing behavior
4. **Project-level support**: Respect project-specific flag settings

## Success Criteria

- Users can set `content-format-mime` flag to enable MIME format globally
- Content tools respect the flag setting and use appropriate formatter
- Default behavior remains unchanged (plain format)
- Project-level flag overrides work correctly
