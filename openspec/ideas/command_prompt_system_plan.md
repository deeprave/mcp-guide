# Command-Based Prompt System Implementation Plan

## Overview
Extend the Guide MCP prompt system to support commands via `:command` and `;command` prefixes, with commands stored as templates in a global `_commands` directory at docroot.

## Requirements Summary
- **Default behavior**: `@guide category1/pattern,category2` → normal content retrieval
- **Command behavior**: `@guide :command` or `@guide ;command` → execute command from `_commands`
- **Command storage**: Global `_commands` directory at docroot (not project-specific)
- **No management**: No config, no special tools, just file-based discovery
- **Template support**: Commands are mustache templates with full context
- **Subcommands**: Support `@guide :command/subcommand` via normal path patterns
- **Error handling**: Return error Result if command doesn't exist (no fallback)
- **Prefix semantics**: `:` official, `;` unofficial (common typo support)
- **Arguments**: Use predefined arg1, arg2, arg3, arg4 pattern like mcp-server-guide

## Architecture Analysis

### Current Guide MCP Structure
- Prompt: `guide` with value parameter and optional arguments
- Current logic: Parse value → route to content retrieval
- Template rendering: Already implemented and working

### Proposed Changes
1. **Prefix Detection**: Check if value starts with `:` or `;`
2. **Command Routing**: Route to `_commands` directory instead of project categories
3. **Path Handling**: Support subcommands via normal file paths
4. **Argument Passing**: Pass prompt arguments to command templates
5. **Auto-discovery**: Scan `_commands` for available commands

## Implementation Strategy

### Phase 1: Core Command Infrastructure
- [ ] Add command prefix detection to guide prompt
- [ ] Implement command routing to `_commands` directory
- [ ] Add error handling for missing commands
- [ ] Test basic command execution

### Phase 2: Template Integration
- [ ] Ensure command templates receive full context
- [ ] Pass prompt arguments to command context
- [ ] Test template rendering in commands
- [ ] Verify context precedence (args override defaults)

### Phase 3: Discovery and Help
- [ ] Implement command auto-discovery
- [ ] Create `:help` command for listing available commands
- [ ] Support subcommand discovery
- [ ] Test command/subcommand path resolution

### Phase 4: Polish and Testing
- [ ] Comprehensive error messages
- [ ] Edge case handling (empty commands, invalid paths)
- [ ] Integration tests with existing guide functionality
- [ ] Documentation and examples

## Technical Details

### Command Detection Logic
```python
def is_command(value: str) -> bool:
    return value.startswith(':') or value.startswith(';')

def extract_command_path(value: str) -> str:
    return value[1:]  # Remove prefix
```

### Command Resolution
- Command path: `_commands/{command_path}.mustache`
- Subcommand path: `_commands/{command}/{subcommand}.mustache`
- Use existing file discovery patterns

### Context Structure
Commands receive standard template context plus:
- `args.arg1`, `args.arg2`, `args.arg3`, `args.arg4` from prompt arguments
- `command.name` - the command name
- `command.path` - full command path

### Error Handling
- Missing command → `Result.failure("Command ':command' not found")`
- Template error → Standard template error handling
- Invalid path → Path validation error

## File Structure
```
docroot/
├── _commands/
│   ├── help.mustache          # :help command
│   ├── create/
│   │   ├── category.mustache  # :create/category
│   │   └── project.mustache   # :create/project
│   └── list/
│       └── projects.mustache  # :list/projects
└── projects/
    └── ... (existing structure)
```

## Testing Strategy

### Unit Tests
- [ ] Command detection logic
- [ ] Command path extraction
- [ ] Error handling for missing commands
- [ ] Template context building

### Integration Tests
- [ ] End-to-end command execution
- [ ] Subcommand resolution
- [ ] Template rendering with arguments
- [ ] Error propagation

### Example Commands to Create
- [ ] `:help` - List available commands
- [ ] `:create/category` - Category creation helper
- [ ] `:list/projects` - Project listing
- [ ] `:status` - System status

## Dependencies
- Existing template rendering system
- File discovery utilities
- Guide prompt infrastructure
- Template context system

## Risks and Mitigations
- **Risk**: Command conflicts with existing content
  - **Mitigation**: Clear prefix separation (: and ;)
- **Risk**: Template errors in commands
  - **Mitigation**: Use existing template error handling
- **Risk**: Performance impact of command discovery
  - **Mitigation**: Cache command list, lazy loading

## Success Criteria
- [ ] Commands execute successfully with `:` and `;` prefixes
- [ ] Subcommands work via path patterns
- [ ] Template rendering works in commands
- [ ] Arguments passed correctly to command context
- [ ] Error handling for missing commands
- [ ] Help system for command discovery
- [ ] No regression in existing guide functionality

## Implementation Notes
- Leverage existing content retrieval patterns
- Minimal changes to current guide prompt structure
- Commands are just special case of content retrieval
- Template system handles all complexity
- File-based approach requires no configuration
