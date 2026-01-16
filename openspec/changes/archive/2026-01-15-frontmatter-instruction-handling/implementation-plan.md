# Implementation Plan: Frontmatter Instruction Handling

## Overview
Fix the core issue where `@guide checks` shows raw frontmatter instead of clean content and ignores frontmatter instructions.

## Implementation Strategy

### Phase 1: Extend Frontmatter Utilities (30 min)
**File**: `src/mcp_guide/utils/frontmatter.py`

Add minimal functions following existing patterns:
```python
def get_frontmatter_instruction(frontmatter: dict) -> str | None:
    return frontmatter.get("instruction")

def get_frontmatter_type(frontmatter: dict) -> str:
    return frontmatter.get("type", "user/information")

def get_type_based_default_instruction(content_type: str) -> str:
    defaults = {
        "user/information": "Display this information to the user",
        "agent/information": "For your information and use. Do not display this content to the user.",
        "agent/instruction": None  # Must use explicit instruction
    }
    return defaults.get(content_type, defaults["user/information"])
```

### Phase 2: Update Content Formatters (45 min)
**Files**: `src/mcp_guide/utils/content_formatter_mime.py`, `content_formatter_plain.py`

Modify both formatters to:
1. Use `parse_frontmatter_content()` to separate frontmatter from content
2. Return only the content body (no frontmatter)
3. Extract instruction for later use

### Phase 3: Update Content Tools (30 min)
**Files**: `src/mcp_guide/tools/tool_content.py`, `tool_category.py`

Modify result construction to:
1. Extract instruction from frontmatter using new utilities
2. Use extracted instruction instead of hardcoded one
3. Apply type-based behavior

### Phase 4: Add Basic Tests (45 min)
**Files**: Test files for modified components

Add minimal tests for:
- Frontmatter instruction extraction
- Content stripping
- Type-based instruction selection

## Key Technical Decisions

1. **Leverage Existing Code**: Use `parse_frontmatter_content()` and `extract_frontmatter()` already in the codebase
2. **Minimal Changes**: Only modify result construction, not the entire content pipeline
3. **Backward Compatibility**: Default to existing behavior for content without frontmatter

## Success Criteria

- `@guide checks` shows clean content without frontmatter delimiters
- System uses frontmatter `instruction` field when present
- Type-based behavior works for all three content types
- Existing content without frontmatter continues to work

## Estimated Total Time: 2.5 hours
