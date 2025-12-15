# Command System TDD Implementation Checklist

## Phase 1: Command Detection (RED-GREEN-REFACTOR)

### Step 1: Command Detection Tests (RED)
- [ ] Test: `is_command()` returns True for `:help`
- [ ] Test: `is_command()` returns True for `;help`
- [ ] Test: `is_command()` returns False for `category`
- [ ] Test: `is_command()` returns False for empty string
- [ ] Test: `extract_command_path()` returns `help` for `:help`
- [ ] Test: `extract_command_path()` returns `create/category` for `:create/category`

### Step 2: Command Detection Implementation (GREEN)
- [ ] Implement `is_command()` function
- [ ] Implement `extract_command_path()` function
- [ ] All detection tests pass

### Step 3: Detection Refactor (REFACTOR)
- [ ] Code quality checks (ruff, mypy)
- [ ] Optimize if needed
- [ ] Update docstrings

## Phase 2: Command Routing (RED-GREEN-REFACTOR)

### Step 4: Command Routing Tests (RED)
- [ ] Test: Guide prompt routes commands to `_commands` directory
- [ ] Test: Guide prompt routes normal values to existing logic
- [ ] Test: Command path resolution works for subcommands
- [ ] Test: Missing command returns appropriate error

### Step 5: Command Routing Implementation (GREEN)
- [ ] Modify guide prompt to detect commands
- [ ] Add command routing logic
- [ ] Implement command path resolution
- [ ] Add error handling for missing commands
- [ ] All routing tests pass

### Step 6: Routing Refactor (REFACTOR)
- [ ] Extract command handling to separate function
- [ ] Ensure clean separation of concerns
- [ ] Code quality checks pass

## Phase 3: Template Integration (RED-GREEN-REFACTOR)

### Step 7: Template Context Tests (RED)
- [ ] Test: Commands receive standard template context
- [ ] Test: Command arguments passed as `args.arg1`, `args.arg2`, etc.
- [ ] Test: Command metadata available (`command.name`, `command.path`)
- [ ] Test: Template rendering works in commands
- [ ] Test: Template errors handled gracefully

### Step 8: Template Integration Implementation (GREEN)
- [ ] Build command context with arguments
- [ ] Add command metadata to context
- [ ] Integrate with existing template rendering
- [ ] All template tests pass

### Step 9: Template Refactor (REFACTOR)
- [ ] Optimize context building
- [ ] Ensure consistent error handling
- [ ] Code quality checks pass

## Phase 4: Command Discovery (RED-GREEN-REFACTOR)

### Step 10: Discovery Tests (RED)
- [ ] Test: `discover_commands()` finds all `.mustache` files in `_commands`
- [ ] Test: Subcommand discovery works for nested directories
- [ ] Test: Command listing excludes non-template files
- [ ] Test: Help command lists available commands

### Step 11: Discovery Implementation (GREEN)
- [ ] Implement command discovery function
- [ ] Create `:help` command template
- [ ] Add command listing to help
- [ ] All discovery tests pass

### Step 12: Discovery Refactor (REFACTOR)
- [ ] Optimize file scanning
- [ ] Cache command list if needed
- [ ] Code quality checks pass

## Phase 5: Integration Testing (RED-GREEN-REFACTOR)

### Step 13: End-to-End Tests (RED)
- [ ] Test: Complete command execution flow
- [ ] Test: Subcommand execution with arguments
- [ ] Test: Error propagation from commands
- [ ] Test: No regression in existing guide functionality
- [ ] Test: Both `:` and `;` prefixes work identically

### Step 14: Integration Implementation (GREEN)
- [ ] Create example commands for testing
- [ ] Ensure all integration scenarios work
- [ ] All end-to-end tests pass

### Step 15: Final Refactor (REFACTOR)
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Code quality final check

## Phase 6: Example Commands (RED-GREEN-REFACTOR)

### Step 16: Example Command Tests (RED)
- [ ] Test: `:help` command lists available commands
- [ ] Test: `:create/category` command with arguments
- [ ] Test: `:list/projects` command shows projects
- [ ] Test: `:status` command shows system info

### Step 17: Example Command Implementation (GREEN)
- [ ] Create `_commands/help.mustache`
- [ ] Create `_commands/create/category.mustache`
- [ ] Create `_commands/list/projects.mustache`
- [ ] Create `_commands/status.mustache`
- [ ] All example commands work

### Step 18: Example Commands Refactor (REFACTOR)
- [ ] Optimize command templates
- [ ] Improve command documentation
- [ ] Code quality final check

## Acceptance Criteria
- [ ] Commands work with `:` and `;` prefixes
- [ ] Subcommands supported via path patterns
- [ ] Arguments passed to command templates
- [ ] Template rendering works in commands
- [ ] Error handling for missing commands
- [ ] Help system for command discovery
- [ ] No regression in existing functionality
- [ ] All tests pass
- [ ] Code quality checks pass

## Files to Modify
- `src/mcp_guide/server.py` (guide prompt)
- `tests/test_guide_prompt.py` (new tests)
- `docroot/_commands/` (command templates)

## Files to Create
- Command detection utilities
- Command discovery functions
- Example command templates
- Integration tests

## Benefits
1. **Extensible**: Easy to add new commands
2. **Template-Powered**: Commands can be dynamic and context-aware
3. **Simple**: File-based, no configuration needed
4. **Consistent**: Uses existing template and content systems
5. **Discoverable**: Help system for command exploration
