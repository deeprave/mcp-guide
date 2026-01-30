# Implementation Tasks

## Core Implementation
- [x] Create `src/mcp_guide/render/` package
- [x] Add frontmatter key constants to `render/content.py` (FM_INSTRUCTION, FM_TYPE, FM_DESCRIPTION, FM_REQUIRES_PREFIX, FM_CATEGORY, FM_USAGE, FM_ALIASES, FM_INCLUDES)
- [x] Add `RenderedContent` dataclass to `render/content.py` (extends `Content`)
- [x] Add `instruction` property to `RenderedContent`
- [x] Add `template_type` property to `RenderedContent`
- [x] Add `render_template()` function to `render/template.py`
- [x] Export from `render/__init__.py`
- [x] Implement frontmatter parsing and `requires-*` checking
- [x] Implement context layering: base (from cache) → frontmatter vars → caller context
- [x] Implement template vs non-template file handling
- [x] Implement error handling: log errors, return None
- [x] Delegate to existing `render_template_content()` for Chevron rendering

## Testing
- [x] Test `requires-*` filtering with project flags
- [x] Test context layering order
- [x] Test template files render with Chevron
- [x] Test non-template files return as-is
- [x] Test partials loading (existing logic)
- [x] Test frontmatter vars in context
- [x] Test `instruction` property (with and without frontmatter value)
- [x] Test `template_type` property (with and without frontmatter value)
- [x] Test error handling (log and return None)

## Documentation
- [x] Update design.md with final implementation notes
- [~] Document `render_template()` API (skipped - covered in README.md)
- [~] Document `RenderedContent` structure (skipped - covered in README.md)
- [~] Document frontmatter key constants (skipped - covered in README.md)

## Integration (Subspec: migrate-content-tools)
- [x] Migrate content tools to use `render_template()` API (see migrate-content-tools/tasks.md)

## Integration (Subspec: migrate-command-rendering)
- [x] Migrate command rendering to use `render_template()` API (see migrate-command-rendering/tasks.md)

## Enhancement (Related: enhance-requires-checking)
- [ ] Enhance `requires-*` checking to support list/dict/key-value requirements (see enhance-requires-checking change)
- [ ] Redesign workflow flag structure to support list/dict/boolean formats
- [ ] Remove legacy `check_frontmatter_requirements()` function
