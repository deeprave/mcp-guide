# Content Management

Understanding how content is organized and delivered in mcp-guide.

## Content Types

mcp-guide organizes content into three types based on purpose and audience:

### user/information

Content displayed directly to users.

**Purpose**: Information the user needs to see and understand.

**Examples**:
- Error messages and warnings
- Status updates and confirmations
- Results and summaries
- User-facing documentation

**Location**: `docroot/user/information/`

**When to use**: When the content should be shown to the human user, not just processed by the agent.

### agent/information

Context and background information for AI agents.

**Purpose**: Help agents understand the project, domain, or task without directing their behavior.

**Examples**:
- Project architecture and design decisions
- Domain knowledge and terminology
- Historical context
- Reference documentation
- Code examples and patterns

**Location**: `docroot/agent/information/`

**When to use**: When the agent needs context to make informed decisions, but you're not telling it what to do.

### agent/instruction

Directives and rules for agent behavior.

**Purpose**: Tell agents how to behave, what to do, and what to avoid.

**Examples**:
- Coding standards and style guides
- Development workflows and processes
- Testing requirements
- Security policies
- Do's and don'ts

**Location**: `docroot/agent/instruction/`

**When to use**: When you need to control or guide agent behavior with explicit rules.

## Why Three Types?

The distinction between these types is important:

1. **Clarity**: Agents know whether content is informational or instructional
2. **Control**: You can provide context without over-constraining behavior
3. **Flexibility**: Mix information and instruction as needed
4. **Organization**: Clear structure makes content easier to manage

## Content Discovery

mcp-guide discovers content through:

1. **Categories** - Define which files to include based on patterns
2. **Collections** - Group categories for specific purposes
3. **Frontmatter** - Metadata in content files controls inclusion

See [Categories and Collections](categories-and-collections.md) for organization details.

## Content Delivery

When an agent requests content:

1. mcp-guide identifies relevant categories/collections
2. Reads matching files from the docroot
3. Processes templates and frontmatter
4. Applies feature flag filters (`requires-*`)
5. Deduplicates instructions
6. Returns formatted content

## Docroot Structure

The docroot is organized by content type:

```
docroot/
├── user/
│   └── information/
│       ├── errors/
│       ├── status/
│       └── results/
├── agent/
│   ├── information/
│   │   ├── architecture/
│   │   ├── domain/
│   │   └── reference/
│   └── instruction/
│       ├── guidelines/
│       ├── workflows/
│       └── standards/
└── commands/
    └── help.mustache
```

## Content Files

Content files can be:

- **Plain text** - Simple text files
- **Markdown** - Formatted documentation
- **Templates** - Mustache/Chevron templates with variables

All files can include frontmatter for metadata and control.

See [Content Documents](content-documents.md) for details on writing content.

## Best Practices

### For user/information

- Be clear and concise
- Use plain language
- Include actionable information
- Format for readability

### For agent/information

- Provide context without prescribing behavior
- Include examples and patterns
- Explain the "why" behind decisions
- Keep it factual and objective

### For agent/instruction

- Be explicit and specific
- Use imperative language ("Do X", "Avoid Y")
- Prioritize important rules
- Keep instructions focused

### General

- Use descriptive filenames
- Organize by topic or domain
- Keep files focused on one topic
- Use templates for dynamic content
- Apply feature flags for conditional content

## Content Organization Tips

1. **Start simple** - Begin with basic categories
2. **Iterate** - Add complexity as needed
3. **Use collections** - Group related categories
4. **Apply YAGNI** - Don't create content you don't need yet
5. **Test with agents** - Verify content is useful

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Organizing content
- **[Content Documents](content-documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion

