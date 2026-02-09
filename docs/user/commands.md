# Commands

Using the guide prompt and command system in mcp-guide.

## What is the Guide Prompt?

The guide prompt is an MCP prompt that provides a command-line interface for interacting with mcp-guide. It allows agents to execute commands and access help.

## Command Invocation

Commands are invoked through the guide prompt:

```
:command [args] [--flags]
```

Examples:

```
:help
:list categories
:show python
```

## Using :help

The `:help` command is your primary discovery mechanism:

```
:help              # Show available commands
:help <command>    # Show command-specific help
```

**Always use :help first** to discover available commands and their usage.

## Command Structure

Commands follow this structure:

```
:command [positional-args] [--flag value] [--boolean-flag]
```

### Positional Arguments

Arguments without flags:

```
:show python        # 'python' is a positional argument
:list categories    # 'categories' is a positional argument
```

### Keyword Arguments

Arguments with flags:

```
:show python --pattern "*.md"
:list --verbose
```

### Boolean Flags

Flags without values (presence = true):

```
:list --verbose
:show --table
```

## Command Context

Commands have access to context variables:

- `command.name` - Command name
- `command.args` - Positional arguments
- `command.kwargs` - Keyword arguments
- `project.*` - Project information
- `workflow.*` - Workflow state (if enabled)
- `session.*` - Session information

## Command Templates

Commands are defined as Mustache templates in `docroot/commands/`.

### Command File Structure

```
docroot/commands/
├── help.mustache       # Help command
├── list.mustache       # List command
└── show.mustache       # Show command
```

### Example Command Template

```mustache
---
type: user/information
description: Show {{command.args.0}} details
---

# {{command.args.0}}

{{#project.categories}}
{{#name_matches}}
**Name**: {{name}}
**Description**: {{description}}
**Directory**: {{dir}}
**Patterns**: {{patterns}}
{{/name_matches}}
{{/project.categories}}
```

## Built-in Commands

### :help

Show available commands or command-specific help.

**Usage**:

```
:help              # List all commands
:help <command>    # Show command help
```

**Examples**:

```
:help
:help list
:help show
```

### Discovery Pattern

The recommended pattern for using commands:

1. Start with `:help` to see available commands
2. Use `:help <command>` for specific command usage
3. Execute the command
4. Use `:help` again if you need more commands

This discovery-first approach helps agents learn available functionality without exhaustive documentation.

## Creating Custom Commands

### 1. Create Command Template

Create a file in `docroot/commands/<command-name>.mustache`:

```mustache
---
type: user/information
description: Custom command description
---

# {{command.name}}

Command output here...

Arguments: {{command.args}}
Flags: {{command.kwargs}}
```

### 2. Use Command Context

Access command arguments and context:

```mustache
{{#command.args}}
Argument: {{.}}
{{/command.args}}

{{#command.kwargs._verbose}}
Verbose mode enabled
{{/command.kwargs._verbose}}
```

### 3. Add Conditional Logic

```mustache
{{#command.kwargs._table}}
| Name | Value |
|------|-------|
{{#items}}
| {{name}} | {{value}} |
{{/items}}
{{/command.kwargs._table}}

{{^command.kwargs._table}}
{{#items}}
- {{name}}: {{value}}
{{/items}}
{{/command.kwargs._table}}
```

## Command Best Practices

### Design

- **Single purpose** - One command, one task
- **Clear naming** - Use descriptive command names
- **Consistent interface** - Follow common patterns
- **Good defaults** - Work without flags when possible

### Help Text

- **Include examples** - Show common usage
- **Document flags** - Explain all options
- **Show output format** - Describe what command returns
- **Link to docs** - Reference detailed documentation

### Output

- **User-friendly** - Format for readability
- **Consistent** - Use consistent formatting
- **Actionable** - Include next steps when relevant
- **Concise** - Don't overwhelm with information

## Examples

### List Categories

```
:list categories
```

Output:

```
Available Categories:
- guidelines: Project guidelines and standards
- python: Python language guidelines
- testing: Testing standards and practices
```

### Show Category Details

```
:show python
```

Output:

```
# python

**Description**: Python language guidelines
**Directory**: lang/python
**Patterns**: *.md, *.txt
**Files**: 5 files found
```

### Verbose Output

```
:show python --verbose
```

Output includes file list and additional details.

## Troubleshooting

### Command Not Found

Check:
1. Command file exists in `docroot/commands/`
2. Filename matches command name
3. File has `.mustache` extension

### Command Not Working

Verify:
1. Template syntax is correct
2. Context variables exist
3. Frontmatter is valid YAML

### Help Not Showing

Ensure:
1. `help.mustache` exists in `docroot/commands/`
2. Template is properly formatted
3. Command files have descriptions

## Next Steps

- **[Content Documents](content-documents.md)** - Writing command templates
- **[Content Management](content-management.md)** - Understanding content types
- **[Developer Documentation](../developer/command-authoring.md)** - Advanced command authoring

