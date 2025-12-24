# Frontmatter Instruction Handling Specification

## Overview

This specification defines how the content system should process frontmatter to extract instructions and handle different content types appropriately.

## Frontmatter Processing

### Content Stripping
- Frontmatter MUST be stripped from content output
- Only the content body should be returned to users/agents
- Frontmatter should be processed separately for metadata extraction

### Instruction Extraction
- The `Instruction` field from frontmatter MUST be used as the Result instruction
- If no `Instruction` field exists, fall back to type-based default instructions
- When processing multiple documents, instructions MUST be deduplicated

### Type-Based Behavior

The system MUST handle content types as follows:

#### `user/information`
- **Content**: Display to user
- **Default Instruction**: "Display this information to the user"
- **Behavior**: Content is meant for user consumption

#### `agent/information`
- **Content**: Process but don't display
- **Default Instruction**: "For your information and use. Do not display this content to the user."
- **Behavior**: Content provides context to agent without user display

#### `agent/instruction`
- **Content**: Process but don't display
- **Default Instruction**: Use frontmatter `Instruction` field
- **Behavior**: Content contains instructions for agent behavior

## Implementation Requirements

### Frontmatter Parser Enhancement
- **Leverage existing utilities**: Use `extract_frontmatter()` and `parse_frontmatter_content()`
- **Add new functions**: `get_frontmatter_instruction()`, `get_frontmatter_type()` (following pattern of existing `get_frontmatter_description()`)
- Validate content type values
- Handle missing or malformed frontmatter gracefully (already handled by existing code)

### Content Formatter Updates
- Strip frontmatter from output content
- Process frontmatter metadata separately
- Apply type-based instruction logic

### Result Construction
- Use extracted instruction from frontmatter
- Deduplicate instructions across multiple documents
- Combine instructions when different types are mixed

## Backward Compatibility

- Existing content without frontmatter continues to work
- Default behavior for unknown types falls back to `user/information`
- Malformed frontmatter doesn't break content processing
