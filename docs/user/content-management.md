# Content Management

Understanding how content is organised and delivered in mcp-guide.

## Document Frontmatter

Documents use YAML frontmatter (metadata at the start of files) to control behaviour and classification. Common keys include:

- **type**: Content classification (required)
- **description**: Human-readable description
- **instruction**: Specific directives for agents

Other frontmatter keys exist and are documented where relevant.

## Content Types

Content type is determined by the `type:` field in document frontmatter (not by directory location). mcp-guide supports three content types:

### user/information

Content displayed directly to users.

**Purpose**: Information the user needs to see and understand.

**Examples**:
- Error messages and warnings
- Status updates and confirmations
- Results and summaries
- User-facing documentation

**When to use**: When the content should be shown to the human user, not just processed by the agent.

### agent/information

Context and background information for AI agents.

**Purpose**: Help agents understand the project, domain, or task without directing their behaviour.

**Examples**:
- Project architecture and design decisions
- Domain knowledge and terminology
- Historical context
- Reference documentation
- Code examples and patterns

**When to use**: When the agent needs context to make informed decisions, but you're not telling it what to do.

### agent/instruction

Directives and rules for agent behaviour.

**Purpose**: Tell agents how to behave, what to do, and what to avoid.

**Examples**:
- Coding standards and style guides
- Development workflows and processes
- Testing requirements
- Security policies
- Do's and don'ts

**When to use**: When you need to control or guide agent behaviour with explicit rules.

## Why Three Types?

The distinction between these types is important:

1. **Clarity**: Agents know whether content is informational or instructional
2. **Control**: You can provide context without over-constraining behaviour
3. **Flexibility**: Mix information and instruction as needed
4. **Organisation**: Clear structure makes content easier to manage

## Supported Formats

Documents can be:

- **Plain markdown** - Formatted documentation
- **Plain text** - Simple text files
- **Mustache templates** - Dynamic content with variables

All files can include frontmatter for metadata and control.

## Content Discovery

mcp-guide discovers content through:

1. **Categories** - Define which files to include based on patterns
2. **Collections** - Group categories for specific purposes
3. **Frontmatter** - Metadata in content files controls inclusion

See [Categories and Collections](categories-and-collections.md) for organisation details.

## Content Delivery

When an agent requests content:

1. mcp-guide identifies relevant categories/collections
2. Reads matching files from the docroot
3. Processes templates and frontmatter
4. Applies feature flag filters
5. De-duplicates instructions
6. Returns formatted content

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Organising content
- **[Content Documents](content-documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion

