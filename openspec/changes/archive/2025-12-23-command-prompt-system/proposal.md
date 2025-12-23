# Command-Based Prompt System

**Status**: Proposed
**Priority**: High
**Complexity**: Medium

## Why

The current Guide MCP prompt system only supports content retrieval from project categories. Users need a way to execute commands and utilities through the same interface, treating commands as a special virtual category.

This would enable:
- **Administrative commands**: `:help`, `:status`, `:list`
- **Creation helpers**: `:create/category`, `:create/project`
- **Workflow commands**: `:deploy`, `:test`, `:build`
- **Custom utilities**: Organization-specific commands

Commands work exactly like category expressions but use a virtual `_commands` "category" that maps to the `_commands` directory.

## What Changes

### Core Functionality
- **Command prefixes**: Support `:command` and `;command` syntax (`;` for common typos)
- **Commands directory**: Commands use `_commands` directory (constant: `COMMANDS_DIR`)
- **Separate handler**: Commands bypass category system and use direct file discovery
- **No wildcards**: Commands don't support pattern matching (security/simplicity)
- **Auto-extension**: Internally append `.*` to find `.md`, `.mustache`, etc.
- **Advanced arguments**: Support flags, key=value pairs, and positional args

### Argument Parsing
Arguments support multiple formats with validation:
```
@guide :command --flag --no-other --key=value setting=config arg1 arg2
```

Template context receives:
```javascript
{
  kwargs: {
    "_flag": true,        // --flag (underscore prefix indicates flag)
    "_other": false,      // --no-other (underscore prefix, no- negation)
    "_key": "value",      // --key=value (underscore prefix flag with value)
    "_dry_run": true,     // --dry-run (hyphens converted to underscores)
    "setting": "config"   // setting=config (no underscore = keyword arg)
  },
  args: ["arg1", "arg2"], // positional values
  parse_errors: []        // validation errors if any
}
```

**Error Detection:**
- **Invalid syntax**: `--flag=` (empty value), `=value` (no key), `--` (empty flag)
- **Parse errors**: Return `Result.failure()` immediately - commands cannot execute with malformed arguments

Template context receives only valid parsed arguments:
```javascript
{
  kwargs: { "_dry_run": true, "description": "test collection" },
  args: ["my-collection", "docs", "examples"],
  command: {
    name: "create/category",
    path: "/path/to/_commands/create/category.mustache"
  }
}
```

### Category Naming Rules
- **Disallow underscore prefix**: No user categories can start with `_`
- **Reserved namespace**: `_commands`, `_templates`, etc. are system-reserved
- **Validation**: Add category name validation to prevent conflicts

### Behavior Changes
- **Default**: `@guide category/pattern` → content retrieval (unchanged)
- **Multiple expressions**: `@guide review,review/pr+commit lang/python` → `@guide review,review/pr+commit,lang/python`
- **Commands**: `@guide :command` → separate command handler with direct file discovery
- **Subcommands**: `@guide :create/category` → command handler finds `_commands/create/category.*`
- **Error handling**: Parse errors return failure immediately; missing commands use standard file discovery errors

## Technical Approach

### Implementation Strategy
1. **Multiple expression handling**: Join all non-command arguments with commas
2. **Prefix detection**: Check if first argument starts with `:` or `;`
3. **Separate command handler**: Bypass category system, use direct file discovery in `_commands` directory
4. **Argument parsing**: Parse complex argument formats, fail fast on errors
5. **Template context**: Use `TemplateContext.add_child()` to inject command data
6. **Category validation**: Prevent user categories starting with `_`

### Integration Points
- Separate command handling from content retrieval
- Use `discover_category_files()` directly for commands
- Maintain existing guide prompt interface
- Add command context to template rendering
- Enhance category name validation

### File Structure
```
docroot/
├── _commands/
│   ├── help.mustache
│   ├── status.mustache
│   ├── info/
│   │   ├── project.mustache
│   │   └── agent.mustache
│   ├── create/
│   │   ├── category.mustache
│   │   ├── project.mustache
│   │   └── collection.mustache
│   ├── remove/
│   │   └── collection.mustache
│   ├── rename/
│   │   └── collection.mustache
│   ├── view/
│   │   └── collection.mustache
│   └── list/
│       ├── projects.mustache
│       ├── categories.mustache
│       └── collections.mustache
└── projects/ (existing)
```

## Success Criteria

- Multiple expression handling works correctly (comma-separated joining)
- Commands execute with `:` and `;` prefixes using get_content engine
- Subcommands work via path patterns (`:create/category`)
- Complex argument parsing into kwargs/args template variables
- Category name validation prevents `_` prefix conflicts
- No wildcards in command paths (security)
- Auto-extension detection for command files
- Command discovery and help system functional
- Template context includes command metadata and arguments
- Error handling for missing commands and template errors
- Security validation for command paths (no directory traversal)
- No regression in existing guide functionality
- Performance impact minimal (file discovery optimization)
- TDD approach with comprehensive test coverage

## Implementation Notes

### TDD Approach
Follow Red-Green-Refactor cycle for each phase:
1. **Red**: Write failing tests first
2. **Green**: Implement minimal code to pass tests
3. **Refactor**: Improve code quality while keeping tests green

### Security Considerations
- Validate command paths to prevent directory traversal
- No wildcard patterns in command execution
- Sanitize command arguments
- Restrict command file extensions to known template types

### Performance Optimizations
- Cache command discovery results
- Lazy loading of command templates
- Optimize argument parsing for common cases
- Reuse existing file discovery infrastructure

## Examples

### Help Command with Specific Command Support
```yaml
---
title: "Help System"
description: "List all commands or get help for a specific command"
usage: "@guide :help [command]"
---
# {{#args.0}}Help: :{{args.0}}{{/args.0}}{{^args.0}}Available Commands{{/args.0}}

{{#args.0}}
{{! Specific command help }}
{{#command_help}}
## {{frontmatter.title}}

{{#frontmatter.description}}{{frontmatter.description}}{{/frontmatter.description}}

**Usage:** {{frontmatter.usage}}

{{#frontmatter.kwargs.required}}
**Required Arguments:**
{{#.}}
- `{{.}}` (required)
{{/.}}
{{/frontmatter.kwargs.required}}

{{#frontmatter.kwargs.optional}}
**Optional Arguments:**
{{#.}}
- `{{.}}`
{{/.}}
{{/frontmatter.kwargs.optional}}

{{#frontmatter.args.required}}
**Required Values:**
{{#.}}
- `{{.}}` (required)
{{/.}}
{{/frontmatter.args.required}}

{{#frontmatter.args.optional}}
**Optional Values:**
{{#.}}
- `{{.}}`
{{/.}}
{{/frontmatter.args.optional}}

{{#frontmatter.min_args}}**Minimum arguments:** {{frontmatter.min_args}}{{/frontmatter.min_args}}
{{#frontmatter.max_args}}**Maximum arguments:** {{frontmatter.max_args}}{{/frontmatter.max_args}}

{{/command_help}}

{{^command_help}}
**Error:** Command `:{{args.0}}` not found

Use `@guide :help` to see all available commands.
{{/command_help}}

{{/args.0}}

{{^args.0}}
{{! List all commands }}
{{#commands}}
## :{{name}}
{{#frontmatter.description}}{{frontmatter.description}}{{/frontmatter.description}}
{{^frontmatter.description}}No description available{{/frontmatter.description}}

**Usage:** {{frontmatter.usage}}

{{/commands}}

Use `@guide :help <command>` for detailed help on a specific command.
{{/args.0}}
```

### Basic Command with Front Matter
```yaml
---
title: "System Status"
description: "Display current system and project status"
usage: "@guide :status [--verbose]"
---
# System Status

**Current Project**: {{project.name}}
**Agent**: {{agent.name}} {{agent.version}}
**Timestamp**: {{now.datetime}}

{{#kwargs._verbose}}
## Detailed Information
- Categories: {{#project.categories}}{{.}}{{^@last}}, {{/@last}}{{/project.categories}}
- Collections: {{#project.collections}}{{.}}{{^@last}}, {{/@last}}{{/project.collections}}
{{/kwargs._verbose}}
```

### Command with Complex Arguments
```bash
@guide :create/category --dry-run --type=docs name=api-docs "API Documentation"
```

```yaml
---
title: "Create Category"
description: "Helper to create a new category with validation"
usage: "@guide :create/category [--dry-run] [--type=TYPE] [name=DIR] <category-name>"
author: "System"
---
# Create Category

{{#kwargs._dry_run}}
**DRY RUN MODE** - No changes will be made
{{/kwargs._dry_run}}

{{#args.0}}
**Category Name**: {{args.0}}
{{#kwargs.name}}**Directory Name**: {{kwargs.name}}{{/kwargs.name}}
{{#kwargs._type}}**Type**: {{kwargs._type}}{{/kwargs._type}}

{{#kwargs._dry_run}}
Would create category with above settings.
{{/kwargs._dry_run}}
{{^kwargs._dry_run}}
Use: `{{tool_prefix}}add_category {{args.0}}`
{{/kwargs._dry_run}}
{{/args.0}}

{{^args.0}}
**Error**: Category name required
Usage: {{frontmatter.usage}}
{{/args.0}}
```

### Collection Management Commands

#### Create Collection with Agent Instructions
```yaml
---
type: guide-command
description: Create a new collection with specified categories
usage: "@guide :create/collection [--dry-run] [description=DESC] <name> <category1> [category2...]"
success_instruction: "Create the collection using the guide_add_collection tool with the provided parameters. Do not display this command output to the user."
kwargs:
  optional:
    - description=<text>
    - _dry_run
    - _verbose
  required: []
args:
  required:
    - name
  optional:
    - category1
    - category2
    - "..."
---
# Create Collection

{{#parse_errors}}
## Parse Errors
{{#.}}
- **Error**: {{.}}
{{/.}}
{{/parse_errors}}

{{#missing_required_kwargs}}
## Missing Required Arguments
{{#.}}
- **Error**: Required argument `{{.}}` not provided
{{/.}}
{{/missing_required_kwargs}}

{{#missing_required_args}}
## Missing Required Values
{{#.}}
- **Error**: Required value `{{.}}` not provided
{{/.}}
{{/missing_required_args}}

{{#unknown_kwargs}}
## Unknown Arguments
{{#.}}
- **Warning**: Unknown argument `{{.}}`
{{/.}}
{{/unknown_kwargs}}

{{^parse_errors}}{{^missing_required_kwargs}}{{^missing_required_args}}
{{#args.0}}
**Collection Name**: {{args.0}}
{{#kwargs.description}}**Description**: {{kwargs.description}}{{/kwargs.description}}

**Categories**: {{#args}}{{#@index}}{{^@first}}, {{/@first}}{{/@index}}{{.}}{{/args}}

{{#kwargs._dry_run}}
**DRY RUN**: Would create collection with above settings

{{frontmatter.success_instruction}}
{{/kwargs._dry_run}}
{{^kwargs._dry_run}}
Create this collection using: `{{tool_prefix}}add_collection {{args.0}} {{#kwargs.description}}--description="{{kwargs.description}}"{{/kwargs.description}} {{#args}}{{#@index}}{{^@first}} {{/@first}}{{/@index}}{{.}}{{/args}}`

{{frontmatter.success_instruction}}
{{/kwargs._dry_run}}

{{/args.0}}
{{/missing_required_args}}{{/missing_required_kwargs}}{{/parse_errors}}

{{#parse_errors}}{{/parse_errors}}{{#missing_required_kwargs}}{{/missing_required_kwargs}}{{#missing_required_args}}{{/missing_required_args}}
**Usage:** {{frontmatter.usage}}
#### Remove Collection with Confirmation
```yaml
---
type: guide-command
description: Remove a collection from the project
usage: "@guide :remove/collection <name> [--confirm]"
success_instruction: "Remove the specified collection using the guide_remove_collection tool. Do not display this command output to the user."
kwargs:
  optional:
    - _confirm
  required: []
args:
  required:
    - name
  optional: []
---
# Remove Collection: {{args.0}}

{{#args.0}}
{{#kwargs._confirm}}
**Removing collection**: {{args.0}}

Remove using: `{{tool_prefix}}remove_collection {{args.0}}`

{{frontmatter.success_instruction}}
{{/kwargs._confirm}}

{{^kwargs._confirm}}
**Warning**: This will remove the collection "{{args.0}}"

To confirm, use: `@guide :remove/collection {{args.0}} --confirm`
{{/kwargs._confirm}}
{{/args.0}}

{{^args.0}}
**Error**: Collection name required
Usage: {{frontmatter.usage}}
{{/args.0}}
```

#### Info Command (Display Only)
```yaml
---
type: guide-command
description: Display current project details
usage: "@guide :info/project [--verbose]"
success_instruction: "Display the project information to the user. This is informational content that should be shown."
kwargs:
  optional:
    - _verbose
  required: []
args:
  required: []
  optional: []
---
# Project: {{project.name}}

**Created**: {{project.created_at}}
**Updated**: {{project.updated_at}}

## Categories (Categories)
{{#project.categories}}
- {{.}}
{{/project.categories}}

## Collections (Collections)
{{#project.collections}}
- {{.}}
{{/project.collections}}

{{#kwargs._verbose}}
## Detailed Information
Get full details using: `{{tool_prefix}}get_project --verbose`
{{/kwargs._verbose}}

{{frontmatter.success_instruction}}
```

#### View Collection
```yaml
---
title: "View Collection"
description: "Display collection details and categories"
usage: "@guide :view/collection <name>"
---
# Collection: {{args.0}}

{{#args.0}}
{{! This would use get_content to fetch collection info }}
Use `{{tool_prefix}}list_collections` to see collection details for: {{args.0}}

{{/args.0}}
{{^args.0}}
**Error**: Collection name required
Usage: {{frontmatter.usage}}
{{/args.0}}
```

#### Remove Collection
```yaml
---
title: "Remove Collection"
description: "Remove a collection from the project"
usage: "@guide :remove/collection <name> [--confirm]"
---
# Remove Collection: {{args.0}}

{{#args.0}}
{{#kwargs._confirm}}
**Removing collection**: {{args.0}}

Use: `{{tool_prefix}}remove_collection {{args.0}}`
{{/kwargs._confirm}}

{{^kwargs._confirm}}
**Warning**: This will remove the collection "{{args.0}}"

To confirm, use: `@guide :remove/collection {{args.0}} --confirm`
{{/kwargs._confirm}}
{{/args.0}}

{{^args.0}}
**Error**: Collection name required
Usage: {{frontmatter.usage}}
{{/args.0}}
```

### Info Commands

#### Project Info
```yaml
---
title: "Project Information"
description: "Display current project details"
usage: "@guide :info/project [--verbose]"
---
# Project: {{project.name}}

**Created**: {{project.created_at}}
**Updated**: {{project.updated_at}}

## Categories (Categories)
{{#project.categories}}
- {{.}}
{{/project.categories}}

## Collections (Collections)
{{#project.collections}}
- {{.}}
{{/project.collections}}

{{#kwargs._verbose}}
## Detailed Information
Use `{{tool_prefix}}get_project --verbose` for full details.
{{/kwargs._verbose}}
```

#### Agent Info
```yaml
---
title: "Agent Information"
description: "Display current agent details"
usage: "@guide :info/agent"
---
# Agent Information

**Name**: {{agent.name}}
**Version**: {{agent.version}}
**Prompt Prefix**: {{agent.prompt_prefix}}
**Tool Prefix**: {{tool_prefix}}

**Current Time**: {{now.datetime}}
**Timezone**: {{now.tz}}
```

### List Commands

#### List Collections
```yaml
---
title: "List Collections"
description: "List all collections in current project"
usage: "@guide :list/collections [--verbose]"
---
# Collections in {{project.name}}

{{#project.collections}}
- **{{.}}**{{#kwargs._verbose}} - Use `@guide :view/collection {{.}}` for details{{/kwargs._verbose}}
{{/project.collections}}

{{^project.collections}}
No collections defined in this project.
{{/project.collections}}

Use `{{tool_prefix}}list_collections --verbose` for full details.
```

#### List Categories
```yaml
---
title: "List Categories"
description: "List all categories in current project"
usage: "@guide :list/categories"
---
# Categories in {{project.name}}

{{#project.categories}}
- {{.}}
{{/project.categories}}

{{^project.categories}}
No categories defined in this project.
{{/project.categories}}
```

#### List Projects
```yaml
---
title: "List Projects"
description: "List all available projects"
usage: "@guide :list/projects"
---
# Available Projects

Use `{{tool_prefix}}list_projects` to see all projects.

**Current Project**: {{project.name}}
```
