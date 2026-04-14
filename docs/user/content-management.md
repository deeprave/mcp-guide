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

Category names can be up to 30 Unicode characters in length and can contain (but not start with) underscores and hyphens.

### Managing Categories

Use the `guide://_project/category` commands to manage categories:

```
guide://_category/list                    # List all categories
guide://_category/add/docs                # Add a new category
guide://_category/add/docs?dir=documentation&patterns=README,CONTRIBUTING
guide://_category/change/docs?new-name=documentation
guide://_category/update/docs?add-patterns=CHANGELOG
guide://_category/remove/docs             # Remove a category
guide://_category/files/docs              # List files in category
```

To see what's in a category, just ask your AI:

```
> list all files in the guide category

Files in the guide category:

1. general (1,946 bytes) - General development guidelines for AI agents
2. methodology - Project methodology policy (injected from selected policies)
```

All files in every category are available to all projects - categories are shared across them. Patterns, however, are defined per-project, so category patterns select the most relevant files for each project. This means referencing a category selectively delivers only the documents most relevant to that project.

## Collections

Each collection is simply a list of expressions used together to return multiple documents. For example, you might define a `self-review` collection containing `[guide/general, checks/instructions, lang/python, review/review]`. Strung together like this, they provide:

- Summary of guidelines
- Special instructions for the current project
- Detailed instructions for producing a code review for a Python project

This enhances the code review with adherence to coding standards and specific edicts that relate to your project.

### Managing Collections

Use the `guide://_project/collection` commands to manage collections:

```
guide://_collection/list                  # List all collections
guide://_collection/add/docs              # Add a new collection
guide://_collection/add/getting-started?categories=docs,guide&description=Beginner%20content
guide://_collection/change/docs?new-categories=docs,guide,lang
guide://_collection/update/docs?add-categories=context
guide://_collection/remove/docs           # Remove a collection
```

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

## Exporting Content

The `export_content` tool allows agents to export rendered content to files for knowledge persistence:

```
export_content(expression="docs", path="documentation.md")
export_content(expression="architecture", path="arch.md", pattern="*.md")
export_content(expression="api-guide", path="api.md", force=True)  # Overwrite existing
```

**Arguments:**

- `expression` - Content expression (category, collection, or pattern)
- `path` - Output filename (required). If no directory component, uses resolved export directory
- `pattern` - Optional glob pattern to filter files
- `force` - Overwrite existing files (default: False)

**Path Resolution:**

- Filename only (`"output.md"`) → prepends resolved export directory
- With directory (`"docs/output.md"`) → uses as-is
- No extension → `.md` added automatically
- Export directory resolution: `path-export` flag → agent default → `.knowledge/`

**Path defaulting:**

When `path` is omitted, the tool uses the `path-export` flag value plus a generated filename based on the expression. For Goose agents, this defaults to `~/.goose/projects/{project-hash}/knowledge/`, allowing knowledge to persist across sessions.

**Export Tracking:**

Exported expressions and their components are tracked automatically. When content is exported, mcp-guide records a metadata hash based on the source files and their modification times. On subsequent exports of the same expression, the hash is compared — if unchanged, the export is skipped with a message directing the agent to the existing file. Use `force=True` to bypass this check.

For agents with knowledge indexing capabilities (such as Kiro and Q Developer), the export template provides instructions to index the exported file into the agent's knowledge base. Once indexed, `get_content` returns a reference to the knowledge entry rather than re-delivering the full content, reducing context usage. The agent can use `force=True` on `get_content` to retrieve the full content when needed.

**Security:**

Export file paths are automatically added to `allowed_write_paths` (the specific file, not the entire directory). Path traversal (`../`, `..\\`) is blocked in path flag values. System directories (`/etc`, `/sys`) are blocked for absolute paths.

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Organising content
- **[Documents](documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion
