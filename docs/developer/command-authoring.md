# Command Template Authoring Guide

This guide explains how to create custom commands using templates with frontmatter specifications.

## Command Structure

Commands are Mustache templates with YAML frontmatter located in the `_commands/` directory under the configured `docroot` (the default location is `~/.config/mcp-guide/docs`):

Each document is prefixed by a "frontmatter" YAML data dictionary, surrounded by three dashes (---) before and after the YAML portion.
The front-matter provides a description of the command, aliases, examples as explained below.
Note that all frontmatter fields are available as context variables within the template.

```mustache
---
description: Brief description of what the command does
category: "system" | "project" | "info" | "list" | "general"
aliases:
  - "shortcut1"
  - "shortcut2"
usage: ":command [options] [args]"
examples:
  - ":command"
  - ":command --flag value"
required_args: []
required_kwargs: []
---
# Command Template Content

Your Mustache template content here...
```

## Frontmatter Fields

### Required Fields
- **description**: Brief description shown in help
- **category**: Command category for organization

### Optional Fields
- **aliases**: Alternative command names
- **usage**: Usage syntax string
- **examples**: List of example invocations
- **required_args**: List of required positional arguments
- **required_kwargs**: List of required keyword arguments

## Template Context

Commands have access to these template variables:

### Command Data
- `{{command.name}}` - Command name
- `{{command.path}}` - Command file path

### Arguments
- `{{args}}` - List of positional arguments
- `{{kwargs}}` - Clean keyword arguments (without underscore prefix)
- `{{raw_kwargs}}` - Original kwargs with underscore prefixes

### Commands List
- `{{commands}}` - All discovered commands
- `{{system_commands}}` - System category commands
- `{{project_commands}}` - Project category commands
- `{{general_commands}}` - General category commands

### Global Context
All template context variables from `get_template_contexts()` are available.

## Example Command

```mustache
---
description: Show project status
category: "project"
aliases: ["st"]
usage: ":status [--verbose]"
examples:
  - ":status"
  - ":status --verbose"
---
# Project Status

{{#kwargs.verbose}}
## Detailed Status
{{/kwargs.verbose}}
{{^kwargs.verbose}}
## Quick Status
{{/kwargs.verbose}}

Current project: **{{project.name}}**

## Categories
{{#project_commands}}
- {{name}} - {{description}}
{{/project_commands}}
```

## Best Practices

1. **Keep descriptions concise** - They appear in help listings
2. **Use appropriate categories** - Helps with command organization
3. **Provide usage examples** - Makes commands discoverable
4. **Validate required arguments** - Use frontmatter validation
5. **Handle missing data gracefully** - Use Mustache conditionals
6. **Test with different contexts** - Ensure templates work across projects

## Mustache Syntax Reference

- `{{variable}}` - Variable interpolation
- `{{#section}}...{{/section}}` - Conditional sections (truthy)
- `{{^section}}...{{/section}}` - Inverted sections (falsy)
- `{{#list}}{{.}}{{/list}}` - Iterate over lists
- `{{! comment }}` - Comments (not rendered)

## Error Handling

Template errors include line context for debugging:

```
Template syntax error in _commands/example.mustache: Unclosed section 'missing'

    12 | {{#section}}
>>> 13 | {{#missing}}
    14 | Content here
    15 | {{/section}}
    16 |
```

## Command Discovery

Commands are automatically discovered from:
- `_commands/*.mustache` files
- Subdirectories: `_commands/category/*.mustache`
- Aliases are resolved during discovery
- File modification times trigger cache invalidation
