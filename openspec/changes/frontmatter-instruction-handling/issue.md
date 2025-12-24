# Frontmatter Instruction Handling Issue

## Problem Statement

The current `get_content` system has several critical issues with frontmatter handling:

1. **Frontmatter Inclusion**: Frontmatter is being included in the content output when it should be processed separately
2. **Instruction Mishandling**: The system uses a hardcoded instruction "Display this information to the user. Take no further action." instead of using the `Instruction` field from frontmatter
3. **Type-Based Behavior Missing**: The system doesn't differentiate between content types (`user/information`, `agent/information`, `agent/instruction`) to determine appropriate handling

## Current Behavior

When running `@guide checks`, the system:
- Returns raw content including frontmatter delimiters
- Ignores the `Instruction` field in frontmatter
- Uses generic instruction regardless of content type
- Doesn't deduplicate instructions when multiple documents are processed

## Expected Behavior

The system should:
- Strip frontmatter from content output
- Use frontmatter `Instruction` field as the Result instruction
- Handle different content types appropriately:
  - `user/information` → "Display this content to the user"
  - `agent/information` → "For your information and use. Do not display this content to the user."
  - `agent/instruction` → Use the frontmatter `Instruction` field
- Deduplicate instructions when processing multiple documents

## Impact

- Users see raw frontmatter instead of clean content
- Agents receive incorrect instructions about how to handle content
- Content type semantics are ignored, leading to inappropriate behavior
