# Content Documents

Document structure, frontmatter, and templates in mcp-guide.

## Document Structure

Content documents consist of two parts:

1. **Frontmatter** - YAML metadata at the top
2. **Content** - The document body

Example:

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

#### type

Content type classification:

```yaml
type: agent/instruction
```

Values:
- `user/information` - User-facing content
- `agent/information` - Agent context
- `agent/instruction` - Agent directives

If omitted, defaults to `agent/instruction`.

#### instruction

Explicit instruction for agents:

```yaml
instruction: Follow TDD principles
```

This overrides type-based default instructions.

#### description

Human-readable description:

```yaml
description: Test-driven development guidelines
```

Used for documentation and discovery.

### Template Variables in Frontmatter

Frontmatter fields support template variables:

```yaml
instruction: Follow {{project.name}} coding standards
description: Guidelines for {{workflow.phase}} phase
```

Variables are expanded when the document is rendered.

## Templates

Template documents MUST have one of the supported Mustache extensions to be rendered as templates:

- `.mustache`
- `.hbs`
- `.handlebars`
- `.chevron`

Without these extensions, documents are treated as plain text/markdown.

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

Include other templates:

```markdown
{{> header}}

Content here...

{{> footer}}
```

## Template Context

Available variables in templates:

### project.*

Project information:

- `{{project.name}}` - Project name
- `{{project.docroot}}` - Docroot path
- `{{project.categories}}` - List of categories
- `{{project.collections}}` - List of collections

### workflow.*

Workflow state (if workflow flag enabled):

- `{{workflow.phase}}` - Current phase (discussion, planning, implementation, check, review)
- `{{workflow.file}}` - Workflow file path
- `{{workflow.next}}` - Next phase
- `{{workflow.consent.exit}}` - Whether consent required to exit phase

### session.*

Session information:

- `{{session.id}}` - Session ID
- `{{session.project}}` - Current project name

### command.*

Command context (in command templates):

- `{{command.name}}` - Command name
- `{{command.args}}` - Command arguments
- `{{command.kwargs}}` - Command keyword arguments

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

## Best Practices

### Frontmatter

- Always include `type` for clarity
- Use `instruction` for explicit directives
- Add `description` for documentation
- Use `requires-*` for conditional content

### Templates

- Keep templates simple
- Use conditionals sparingly
- Document complex logic
- Test with different contexts

### Content

- Write clear, concise content
- Use Markdown formatting
- Structure with headings
- Include examples

### Organisation

- One topic per file
- Use descriptive filenames
- Group related files
- Keep files focused

## Troubleshooting

### Template Not Rendering

Check:
1. Syntax is correct (matching braces)
2. Variable exists in context
3. No typos in variable names

### Frontmatter Not Parsed

Ensure:
1. Frontmatter is at file start
2. Enclosed in `---` markers
3. Valid YAML syntax
4. No tabs (use spaces)

### Content Not Included

Verify:
1. `requires-*` flags match
2. File matches category patterns
3. File is in correct directory

## Next Steps

- **[Feature Flags](feature-flags.md)** - Conditional content with flags
- **[Commands](commands.md)** - Using command templates
- **[Content Management](content-management.md)** - Content types and organisation

