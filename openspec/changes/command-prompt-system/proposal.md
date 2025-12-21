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
- **Virtual category**: Commands use `_commands` directory (no category definition needed)
- **Same engine**: Use existing `get_content` logic with `_commands` as category
- **No wildcards**: Commands don't support pattern matching (security/simplicity)
- **Auto-extension**: Internally append `.*` to find `.md`, `.mustache`, etc.
- **Advanced arguments**: Support flags, key=value pairs, and positional args

### Argument Parsing
Arguments support multiple formats:
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
    "setting": "config"   // setting=config (no underscore = keyword arg)
  },
  args: ["arg1", "arg2"] // positional values
}
```

### Category Naming Rules
- **Disallow underscore prefix**: No user categories can start with `_`
- **Reserved namespace**: `_commands`, `_templates`, etc. are system-reserved
- **Validation**: Add category name validation to prevent conflicts

### Behavior Changes
- **Default**: `@guide category/pattern` → content retrieval (unchanged)
- **Commands**: `@guide :command` → `get_content("_commands/command")`
- **Subcommands**: `@guide :create/category` → `get_content("_commands/create/category")`
- **Error handling**: Standard file not found errors from get_content engine

## Technical Approach

### Implementation Strategy
1. **Prefix detection**: Check if guide prompt value starts with `:` or `;`
2. **Path transformation**: Convert `:command/sub` to `_commands/command/sub`
3. **Argument parsing**: Parse complex argument formats into kwargs/args
4. **Content retrieval**: Use existing get_content with transformed path
5. **Category validation**: Prevent user categories starting with `_`

### Integration Points
- Leverage existing get_content engine completely
- Use current FileInfo and template rendering
- Maintain existing guide prompt interface
- Add argument parsing to template context
- Enhance category name validation

### File Structure
```
docroot/
├── _commands/
│   ├── help.md
│   ├── status.mustache
│   ├── create/
│   │   ├── category.mustache
│   │   └── project.mustache
│   └── list.md
└── projects/ (existing)
```

## Success Criteria

- Commands execute with `:` and `;` prefixes using get_content engine
- Subcommands work via path patterns (`:create/category`)
- Complex argument parsing into kwargs/args template variables
- Category name validation prevents `_` prefix conflicts
- No wildcards in command paths (security)
- Auto-extension detection for command files
- No regression in existing guide functionality
- Reuse existing template rendering and FileInfo systems

## Examples

### Basic Command
```mustache
{{! _commands/status.mustache }}
# System Status

**Current Project**: {{project.name}}
**Agent**: {{agent.name}} {{agent.version}}
**Timestamp**: {{now.datetime}}

{{#kwargs._verbose}}
## Detailed Information
- Categories: {{project.categories.length}}
- Collections: {{project.collections.length}}
{{/kwargs._verbose}}
```

### Command with Complex Arguments
```bash
@guide :create/category --dry-run --type=docs name=api-docs "API Documentation"
```

```mustache
{{! _commands/create/category.mustache }}
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
Usage: `@guide :create/category [--dry-run] [--type=TYPE] [name=DIR] <category-name>`
{{/args.0}}
```
