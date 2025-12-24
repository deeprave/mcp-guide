# Frontmatter Instruction Handling Tasks

## Task 1: Extend Frontmatter Utilities
**File**: `src/mcp_guide/utils/frontmatter.py`
**Priority**: High
**Estimated Effort**: 1-2 hours

Add new functions following existing patterns:
- [ ] Add `get_frontmatter_instruction()` function (similar to `get_frontmatter_description()`)
- [ ] Add `get_frontmatter_type()` function
- [ ] Add `get_type_based_default_instruction()` function
- [ ] Add content type constants (`USER_INFO`, `AGENT_INFO`, `AGENT_INSTRUCTION`)
- [ ] Add `validate_content_type()` function

## Task 2: Update Content Processing
**File**: `src/mcp_guide/utils/content_common.py`
**Priority**: High
**Estimated Effort**: 2-3 hours

Update content processing to handle frontmatter:
- [ ] Update `read_and_render_file_contents()` to use `parse_frontmatter_content()`
- [ ] Strip frontmatter from content output
- [ ] Add instruction extraction and deduplication logic
- [ ] Handle multiple document instruction merging

## Task 3: Update Content Formatters
**Files**: `src/mcp_guide/utils/content_formatter_*.py`
**Priority**: Medium
**Estimated Effort**: 1-2 hours

Enhance formatters to process frontmatter:
- [ ] Strip frontmatter from content output in both formatters
- [ ] Extract and process frontmatter metadata
- [ ] Apply type-based instruction logic

## Task 4: Update Get Content Tool
**File**: `src/mcp_guide/tools/tool_content.py`
**Priority**: High
**Estimated Effort**: 1 hour

Integrate frontmatter processing:
- [ ] Use extracted instructions from frontmatter
- [ ] Apply type-based result construction
- [ ] Handle instruction deduplication

## Task 5: Update Category Content Tool
**File**: `src/mcp_guide/tools/tool_category.py`
**Priority**: High
**Estimated Effort**: 1 hour

Apply frontmatter processing to category content:
- [ ] Use same frontmatter processing logic as get_content
- [ ] Ensure consistent behavior across content tools

## Task 6: Unit Tests
**Files**: Various test files
**Priority**: High
**Estimated Effort**: 3-4 hours

Comprehensive test coverage:
- [ ] Test frontmatter instruction extraction
- [ ] Test content type validation
- [ ] Test instruction deduplication
- [ ] Test content stripping
- [ ] Test type-based behavior for all content types

## Task 7: Integration Tests
**File**: `tests/integration/test_frontmatter_processing.py` (new)
**Priority**: Medium
**Estimated Effort**: 2-3 hours

End-to-end testing:
- [ ] Test `@guide checks` command behavior
- [ ] Test mixed content type handling
- [ ] Test backward compatibility with content without frontmatter
