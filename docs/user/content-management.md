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
| `cache` | Optional response-cache policy for document content |

Other metadata keys are used for specific purposes: `tags`, `title`, `requires-<feature-flag>`, `includes` (for partial templates). Commands use additional keys like `category`, `aliases`, `usage`, and `examples`.

**Note on using `instruction`**: A default instruction is automatically applied based on the value in its `type`.
This means that `instruction` should only be used to vary that in some way, or add additional instruction.
If the document has `type: agent/instruction` (and most are), the document's content is read as an instruction and can contain the additional context there.

### Document cache policies

Ordinary non-template Markdown defaults to `long, public` because Guide delivers its
exact document content. Other documents are not cacheable unless they explicitly declare
`cache`. Use `long` for content that changes rarely (24 hours), `medium` for content likely to change with
project settings (15 minutes), or `short` for safely reusable dynamic content (2
minutes). Scope is `public` by default; add `private` for output that depends on
feature flags, project settings, or conditional `requires-*` rendering.

```yaml
cache: long
cache: medium, private
cache: public             # equivalent to medium, public
cache: shared             # alias for public
cache: no-cache
```

When a document renders partials, every rendered part participates: an omitted or
`no-cache` rendered-template policy disables caching for the combined response; otherwise the shortest
TTL and the most restrictive scope win. Commands and prompts do not expose document
cache policies. When the content format is MIME, each document part also carries its
own standard `Cache-Control` header, so mixed-policy responses remain individually
cacheable where appropriate.

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

The `export_content` tool returns rendered content and delivery frontmatter for a
client to save. Guide does not write, track, or inspect the resulting client file.

For a project with `.todo/` in its configured `allowed_write_paths`:

```python
export_content(expression="docs", path=".todo/documentation.md")
export_content(expression="architecture", path=".todo/architecture", pattern="*.md")
export_content(expression="api-guide", path=".todo/api.md", force=True)
```

**Arguments:**

- `expression` - Content expression (category, collection, or pattern)
- `path` - Required client destination, used exactly as supplied; no default
  directory or extension is added
- `pattern` - Optional glob pattern to filter files
- `force` - Instruct the client to overwrite an existing file; otherwise create
  only and report an existing destination without overwriting it

**Destination policy:**

The destination must match a configured write-file entry or lie within a
configured write-directory entry. Guide rejects uncovered destinations,
including otherwise permitted temporary paths, without adding permissions.
Filesystem roots (including equivalent spellings, drive roots and UNC share
roots) cannot be configured as write entries. Export destinations containing
ASCII controls or backticks are rejected with a fixed error that does not echo
the destination. Path traversal is rejected. Permission changes are separate administrative
operations when authentication is active; admin access does not bypass this
export check. Guide checks the configured paths lexically, not against the
server's filesystem. The client remains responsible for performing the write.

**Content handling:**

Write the complete returned payload verbatim. Its YAML frontmatter carries the
resolved `type` and `instruction` for later handling; these are file data, not
instructions to execute while exporting. Follow the tool's separate write
instruction and report client-side success or failure.

Every export returns current rendered content. Guide remembers no destination,
timestamp or source hash, and does not manage subsequent client indexing or
caching. Later `get_content` calls and equivalent content URIs always retrieve
content from Guide, never substitute a prior exported or indexed copy. Export
has no mutation-based authentication requirement, but its destination policy
still applies.

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Organising content
- **[Documents](documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion
