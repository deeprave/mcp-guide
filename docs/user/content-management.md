# Content Management

Understanding how your content gets organised and delivered to your AI agent.

## Projects

mcp-guide organizes everything around **projects**. A project is typically tied to the basename of your current directory - if you're working in `/home/user/my-app`, your project is `my-app`.

Categories and collections are configured per-project. This means each project can have its own patterns and groupings, even though the underlying documents are shared across all projects.

Behind the scenes, mcp-guide uses a hash calculated from the absolute path to uniquely identify each project. This means you can have two projects with the same name in different filesystem locations, and they'll be treated as separate projects with their own configurations.

## Document Format

mcp-guide works primarily with markdown files, though any text file can serve as a source of information. Mustache templates are rendered to markdown before delivery.

Documents can include optional **metadata** (called "frontmatter") - a YAML block at the top of the file delimited by three hyphens above and below:

```markdown
---
type: agent/instruction
description: Python coding standards
instruction: Follow these standards when writing Python code
---

# Python Standards

Your content here...
```

### Common Metadata Keys

| Key | Purpose |
|-----|---------|
| `type` | Document type (see below) - determines how content is used |
| `description` | Human-readable description of the document |
| `instruction` | Specific directive for the agent (not always required) |

Other metadata keys are used for specific purposes: `tags`, `title`, `requires-<feature-flag>`, `includes` (for partial templates). Commands use additional keys like `category`, `aliases`, `usage`, and `examples`.

**Note on using `instruction`**: A default instruction is automatically applied based on the value in its `type`.
This means that `instruction` should only be used to vary that in some way, or add additional instruction.
If the document has `type: agent/instruction` (and most are), the document's content is read as an instruction and can contain the additional context there.

## Document Types

The `type` metadata key determines how content is used:

| Type | Purpose | Audience |
|------|---------|----------|
| `user/information` | Display rendered information to the user | Human user |
| `agent/information` | Provide context and additional information | AI agent |
| `agent/instruction` | Direct the agent to execute given instructions | AI agent |

The distinction is simple but powerful - it tells the agent whether content is for display, context, or direction.

## Document Categories

Documents belong to a **category**. Each category represents a directory structure in the document store where documents can be retrieved. Categories are assigned patterns for files within them that are displayed *by default* when the category is referenced. However, all files in a category are always available by overriding the pattern with `<category>[/pattern1[+pattern2...]]`. This is called a document **expression**.

Category names can be up to 30 unicode characters in length and can contain (but not start with) underscores and hyphens.

To see what's in a category, just ask your AI:

```
> list all files in the guide category

Files in the guide category:

1. bdd (1,811 bytes) - Principles and practices of BDD
2. general (1,946 bytes) - General development guidelines for AI agents
3. tdd (1,329 bytes) - Principles and practices of TDD
4. yagni (2,815 bytes) - Principle of avoiding unnecessary complexity
5. ddd (2,504 bytes) - Principles and patterns of Domain-Driven Design
6. solid (2,237 bytes) - Five principles of object-oriented design
```

All files in every category are available to all projects - categories are shared across them. Patterns, however, are defined per-project, so category patterns select the most relevant files for each project. This means referencing a category selectively delivers only the documents most relevant to that project.

## Collections

Each collection is simply a list of expressions used together to return multiple documents. For example, you might define a `self-review` collection containing `[guide/general, checks/instructions, lang/python, review/review]`. Strung together like this, they provide:

- Summary of guidelines
- Special instructions for the current project
- Detailed instructions for producing a code review for a Python project

This enhances the code review with adherence to coding standards and specific edicts that relate to your project.

## Content Concatenation

When multiple documents are requested, they're concatenated and presented to the agent. The `content-format` feature flag controls how this happens:

- **None** - Documents concatenated with no delimiters
- **plain** - Simple text separators between documents
- **mime** - MIME-style delimiters with metadata headers

Different agents prefer different formats. Experiment to determine the setting that gives the best results with your agent.

## Content Style

The `content-style` flag affects how markdown is rendered to the console. Agents render markdown differently - some have complete support for headings, bolding, and italics.

For documents delivered to the console (to the user), the style should match your client:

- **full** - Complete markdown rendering (works well with Claude Code)
- **headings** - Only render header markup
- **plain** - (default) Don't render content as headings, bold or italic

Choose according to your agent's capabilities and your taste.

## Content Discovery

mcp-guide discovers content through:

1. **Categories** - Define which files to include based on patterns
2. **Collections** - Group category expressions for specific purposes
3. **Metadata** - Frontmatter controls inclusion and behaviour

See [Categories and Collections](categories-and-collections.md) for organisation details.

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Organising content
- **[Documents](documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion
