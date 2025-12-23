# Template Extension Support

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

Currently, the template system only recognizes `.mustache` files as templates. However, there are other common extensions used in the Mustache/Handlebars ecosystem:

- `.hbs` - Standard Handlebars extension (widely used)
- `.handlebars` - Alternative Handlebars extension
- `.chevron` - Could be useful for clarity when using the Chevron library

This limitation means users familiar with other templating conventions cannot use their preferred file extensions, and existing templates from other projects may need to be renamed.

## What Changes

- Extend `TEMPLATE_EXTENSION` constant to support multiple extensions
- Update file discovery logic to recognize `.mustache`, `.hbs`, `.handlebars`, and optionally `.chevron` files
- Ensure template rendering works consistently across all supported extensions
- Update documentation to reflect supported extensions

## Technical Approach

1. Replace single `TEMPLATE_EXTENSION` constant with `TEMPLATE_EXTENSIONS` list
2. Update `file_discovery.py` pattern matching to handle multiple extensions
3. Update `template_renderer.py` `is_template_file()` function
4. Ensure backward compatibility with existing `.mustache` files
5. Add tests for all supported extensions

## Success Criteria

- All existing `.mustache` templates continue to work unchanged
- New templates can use `.hbs`, `.handlebars`, and `.chevron` extensions
- Template discovery and rendering works identically across all extensions
- Documentation updated with supported extensions list
