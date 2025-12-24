# Implementation Plan: Frontmatter Instruction Handling

## Phase 1: Frontmatter Processing Enhancement

### 1.1 Extend Existing Frontmatter Utilities
- **File**: `src/mcp_guide/utils/frontmatter.py`
- **Changes** (leveraging existing `extract_frontmatter()` and `parse_frontmatter_content()`):
  - Add `get_frontmatter_instruction()` function (similar to existing `get_frontmatter_description()`)
  - Add `get_frontmatter_type()` function
  - Add `get_type_based_default_instruction()` function

### 1.2 Content Type Constants and Validation
- **File**: `src/mcp_guide/utils/frontmatter.py`
- **Changes**:
  - Add content type constants (`USER_INFO`, `AGENT_INFO`, `AGENT_INSTRUCTION`)
  - Add `validate_content_type()` function
  - Add fallback logic for unknown types

## Phase 2: Content Processing Updates

### 2.1 Content Formatter Enhancement
- **File**: `src/mcp_guide/utils/content_formatter_*.py`
- **Changes**:
  - Strip frontmatter from content output
  - Extract and process frontmatter metadata
  - Apply type-based instruction logic

### 2.2 Content Common Updates
- **File**: `src/mcp_guide/utils/content_common.py`
- **Changes**:
  - Update `read_and_render_file_contents()` to use existing `parse_frontmatter_content()`
  - Strip frontmatter from content using existing parsing logic
  - Add instruction extraction and deduplication logic using new frontmatter functions
  - Handle multiple document instruction merging

## Phase 3: Tool Integration

### 3.1 Get Content Tool Updates
- **File**: `src/mcp_guide/tools/tool_content.py`
- **Changes**:
  - Use extracted instructions from frontmatter
  - Apply type-based result construction
  - Handle instruction deduplication

### 3.2 Category Content Tool Updates
- **File**: `src/mcp_guide/tools/tool_category.py` (category_content function)
- **Changes**:
  - Apply same frontmatter processing logic
  - Ensure consistent behavior across content tools

## Phase 4: Testing

### 4.1 Unit Tests
- Test frontmatter instruction extraction
- Test content type validation
- Test instruction deduplication
- Test content stripping

### 4.2 Integration Tests
- Test `@guide checks` command behavior
- Test mixed content type handling
- Test backward compatibility

## Implementation Order

1. **Frontmatter utilities** (Phase 1)
2. **Content processing** (Phase 2)
3. **Tool integration** (Phase 3)
4. **Testing** (Phase 4)

## Risk Mitigation

- Maintain backward compatibility with existing content
- Graceful handling of malformed frontmatter
- Default fallbacks for missing metadata
- Comprehensive test coverage for edge cases
