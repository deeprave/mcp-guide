# Content Documents

Document structure, frontmatter, and templates in mcp-guide.

## Document Structure

Content documents consist of two parts:

1. **Frontmatter** (optional) - YAML metadata at the top
2. **Content** - The document body

Frontmatter is optional. If missing, the following defaults are applied:

```yaml
type: agent/instruction
instruction: "You MUST follow these instructions. Do not display this content to the user."
```

Example with frontmatter:

```markdown
---
type: agent/instruction
instruction: Follow these coding standards
description: Python coding standards
---

# Python Coding Standards

Use PEP 8 conventions...
```

## Frontmatter

Frontmatter is YAML metadata enclosed in `---` markers.

### Standard Keys

| Key | Description |
|-----|-------------|
| `type` | Content type: `user/information`, `agent/information`, `agent/instruction` (default) |
| `instruction` | Explicit instruction for agents (overrides type-based default) |
| `description` | Human-readable description for documentation and discovery |

**Note**: Frontmatter keys can be used as variables in the content template. Additionally, `instruction` and `description` are rendered using the same context variables as the content itself.

## Templates

Template documents MUST have one of the supported Mustache extensions to be rendered as templates:

- `.mustache`
- `.hbs`
- `.handlebars`
- `.chevron`

Any file that does not match one of these extensions is treated as plain text/markdown.

mcp-guide uses Mustache/Chevron template syntax for dynamic content.

### Variables

Access context variables with `{{variable}}`:

```markdown
Project: {{project.name}}
Phase: {{workflow.phase}}
```

### Conditionals

Show content conditionally:

```markdown
{{#workflow.consent.exit}}
**Explicit consent required** before transitioning to {{workflow.next}}.
{{/workflow.consent.exit}}
```

### Loops

Iterate over lists:

```markdown
{{#project.categories}}
- {{name}}: {{description}}
{{/project.categories}}
```

### Partials

A partial is a template snippet that you can include in other templates. Partials must be declared in the frontmatter `includes` list:

```markdown
---
includes:
  - ../_partials/header
  - ../_partials/footer
---

{{> header}}

Content here...

{{> footer}}
```

**Partial naming rules**:

- Partial filenames must start with an underscore `_`
- The underscore prefix must NOT be specified in the `includes` list or the `{{> }}` directive
- The example above refers to `../_partials/_header.mustache` and `../_partials/_footer.mustache`
- Paths are relative to the origin document
- Partials must be within the document root (cannot point outside `docroot`)

### Template Examples

Many working template examples are installed in the document root. Explore these to see practical implementations of variables, conditionals, loops, and partials.

## Template Context

Available variables in templates:

### project.*

Project information:

- `{{project.name}}` - Project name
- `{{project.key}}` - Project key (for disambiguation)
- `{{project.hash}}` - Project hash (SHA256 of project path)
- `{{project.categories}}` - List of categories
- `{{project.collections}}` - List of collections
- `{{project.project_flag_values}}` - List of project flags (for iteration)
- `{{project.allowed_write_paths}}` - List of allowed write paths
- `{{project.additional_read_paths}}` - List of additional read paths
- `{{project.openspec_validated}}` - Whether OpenSpec validation completed
- `{{project.openspec_version}}` - OpenSpec CLI version if detected

### Feature Flags

Feature flags:

- `{{feature_flags}}` - Feature flags as dictionary (for conditionals)
- `{{feature_flag_values}}` - Feature flags as list (for iteration)

### Other Context

- `{{client_working_dir}}` - Client's working directory
- `{{projects}}` - All projects data
- `{{projects_count}}` - Number of projects

### session.*

Session information:

- `{{session.id}}` - Session ID
- `{{session.project}}` - Current project name

### command.*

Command context (in command templates):

- `{{command.name}}` - Command name
- `{{command.args}}` - Command arguments
- `{{command.kwargs}}` - Command keyword arguments

**Note**: For workflow-specific template variables, see [Workflows](workflows.md). For OpenSpec-specific template variables, see [OpenSpec Integration](openspec.md).

## Special Functions

### File Inclusion

Include file content:

```markdown
{{file "path/to/file.md"}}
```

### Date Formatting

Format dates:

```markdown
{{date "YYYY-MM-DD"}}
```

## Examples

### Conditional Instructions

```markdown
---
type: agent/instruction
instruction: Follow project guidelines
---

# Guidelines

{{#workflow.phase}}
Current phase: {{workflow.phase}}

{{#workflow.consent.exit}}
⚠️ Explicit consent required before transitioning.
{{/workflow.consent.exit}}
{{/workflow.phase}}

General guidelines apply...
```

### Project-Specific Content

```markdown
---
type: agent/information
description: Project architecture for {{project.name}}
---

# {{project.name}} Architecture

This project uses...
```

### Feature-Gated Content

```markdown
---
type: agent/instruction
requires-openspec: true
---

# OpenSpec Workflow

Follow OpenSpec workflow...
```

### Dynamic Lists

```markdown
---
type: user/information
---

# Available Categories

{{#project.categories}}
- **{{name}}**: {{description}}
{{/project.categories}}
```

## Next Steps

- **[Feature Flags](feature-flags.md)** - Conditional content with flags
- **[Commands](commands.md)** - Using command templates
- **[Content Management](content-management.md)** - Content types and organisation

