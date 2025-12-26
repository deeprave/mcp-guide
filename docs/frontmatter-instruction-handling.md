# Frontmatter Instruction Handling

The MCP Guide system supports YAML frontmatter in content files to control how content is processed and what instructions are provided to agents.

## Overview

Frontmatter is stripped from content output and processed separately to extract metadata including instructions for agent behavior. This allows content authors to specify how agents should handle different types of content.

## Content Types

The system supports three content types that determine default behavior:

### `user/information` (default)
Content intended for user display.
- **Default instruction**: "Display this information to the user"
- **Behavior**: Content is shown to the user

### `agent/information`
Content that provides context to the agent without user display.
- **Default instruction**: "For your information and use. Do not display this content to the user."
- **Behavior**: Agent processes content but doesn't show it to user

### `agent/instruction`
Content that contains explicit instructions for agent behavior.
- **Default instruction**: Uses explicit `instruction` field from frontmatter
- **Behavior**: Agent follows the specified instructions

## Frontmatter Fields

### `type`
Specifies the content type (optional, defaults to `user/information`).

```yaml
---
type: agent/information
---
```

### `instruction`
Explicit instruction for how the agent should handle the content.

```yaml
---
instruction: "Process this content carefully and summarize the key points"
---
```

### `partials`
References to partial templates for future template composition (basic parsing only).

```yaml
---
partials:
  header: "templates/partials/header.md"
  footer: "templates/partials/footer.md"
---
```

## Important Instructions

Instructions can be marked as "important" by prefixing with `!`. Important instructions override all regular instructions when multiple files are processed.

### Regular Instructions
```yaml
---
instruction: "Display this to the user"
---
```

### Important Instructions
```yaml
---
instruction: "! This is critical - process immediately"
---
```

## Instruction Processing

When multiple files are processed:

1. **Regular instructions** are accumulated and deduplicated
2. **Important instructions** (starting with `!`) override all regular instructions
3. **Multiple important instructions** are combined (regular instructions ignored)
4. **Instructions are separated by newlines** in the final output
5. **Insertion order is preserved** (no alphabetical sorting)

## Examples

### Basic Content Type Usage

```yaml
---
type: user/information
---
# Welcome Guide
This content will be displayed to the user.
```

```yaml
---
type: agent/information
---
# Internal Notes
This provides context to the agent but won't be shown to the user.
```

### Explicit Instructions

```yaml
---
type: agent/instruction
instruction: "Summarize this content in bullet points"
---
# Technical Documentation
Complex technical content here...
```

### Important Instructions Override

**File 1:**
```yaml
---
instruction: "Display normally"
---
Regular content
```

**File 2:**
```yaml
---
instruction: "! Critical: Handle with special care"
---
Important content
```

**Result**: Only the important instruction is used: "Critical: Handle with special care"

### Multiple Important Instructions

**File 1:**
```yaml
---
instruction: "! First critical instruction"
---
Content 1
```

**File 2:**
```yaml
---
instruction: "! Second critical instruction"
---
Content 2
```

**Result**: Both important instructions combined:
```
First critical instruction
Second critical instruction
```

## Implementation Details

- Frontmatter is parsed using YAML and stripped from content output
- Content type validation ensures only supported types are used
- Instruction extraction follows a priority system (explicit > type-based defaults)
- Important instruction detection uses pre-compiled regex for performance
- All processing maintains backward compatibility with content lacking frontmatter

## Related Features

- **Template Support**: Frontmatter works with template rendering
- **Partial Templates**: Basic parsing support for future template composition
- **Content Formatting**: Works with both plain text and MIME formatters
- **Tool Integration**: Automatically used by content retrieval tools
