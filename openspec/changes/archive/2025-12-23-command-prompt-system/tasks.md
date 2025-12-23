# Command-Based Prompt System - Implementation Tasks

## Phase 1: Category Name Validation ✓ COMPLETED
- [x] Add validation to prevent user categories starting with `_`
- [x] Update category creation tools to reject underscore prefixes
- [x] Add validation to existing category management functions
- [x] Test category name validation with various underscore patterns
- [x] Update error messages for invalid category names

## Phase 2: Guide Prompt Enhancement ✓ COMPLETED
- [x] Add multiple expression handling (join arguments with commas)
- [x] Add command prefix detection (`:` and `;`) to guide prompt parsing
- [x] Implement path transformation from `:command/sub` to `_commands/command/sub`
- [x] Add command path validation (no wildcards, security checks)
- [x] Test prefix detection and path transformation logic
- [x] Test multiple expression joining for normal content retrieval
- [x] Handle edge cases (empty commands, malformed paths)

## Phase 3: Advanced Argument Parsing ✓ COMPLETED
- [x] Implement argument parser for `--flag`, `--no-flag`, `--key=value` formats
- [x] Add support for `key=value` pairs without dashes
- [x] Separate positional arguments from flag/key arguments
- [x] Build kwargs and args template context structure
- [x] Add argument validation against front matter specification
- [x] Support `required_kwargs`, `optional_kwargs`, `required_flags`, `optional_flags`
- [x] Collect missing required arguments in validation arrays
- [x] Collect unknown kwargs/flags in `unknown_kwargs` and `unknown_flags` arrays
- [x] Validate argument count against `min_args` and `max_args`
- [x] Generate `arg_count_error` message for invalid argument counts
- [x] Handle invalid syntax: empty values, malformed flags, missing keys
- [x] Collect parse errors in `parse_errors` array for template access
- [x] Test complex argument parsing scenarios
- [x] Handle edge cases: quoted arguments, special characters, empty values

## Phase 4: Separate Command Handler ✓ COMPLETED
- [x] Add `COMMANDS_DIR = "_commands"` constant
- [x] Create separate `handle_command()` function in guide prompt
- [x] Use file discovery utilities directly (bypass category system)
- [x] Remove command routing through get_content virtual category
- [x] Ensure FileInfo.category is empty or None for commands
- [x] Test command execution with direct file discovery
- [x] Verify no impact on existing get_content functionality

## Phase 5: Template Context Enhancement ✓ COMPLETED
- [x] Add `kwargs` and `args` to template context for commands
- [x] Ensure command templates receive full standard template context
- [x] Add command metadata (`command.name`, `command.path`) to context
- [x] Use `TemplateContext.add_child()` for proper context layering
- [x] Implement fail-fast error handling for parse errors
- [x] Test argument access in command templates
- [x] Verify context precedence and override behavior

## Phase 6: Command Discovery and Help System ✓ COMPLETED
- [x] Implement command auto-discovery in `_commands` directory
- [x] Support subcommand discovery for nested directories
- [x] Extract front matter from command files for metadata
- [x] Create `:help` command template that lists discovered commands
- [x] Add specific command help: `@guide :help <command>` shows detailed info
- [x] Provide `commands` array to help template with name and front matter
- [x] Add command description support via front matter `description` field
- [x] Add command usage examples via front matter `usage` field
- [x] Test help system with nested command structure
- [x] Handle commands without front matter gracefully
- [x] Handle non-existent commands in specific help requests

## Phase 7: Error Handling and Security ✓ COMPLETED
- [x] Handle missing command files through get_content error system
- [x] Add validation for command path security (no directory traversal)
- [x] Test malformed argument parsing edge cases
- [x] Handle template errors in command execution
- [x] Add comprehensive error messages for command issues
- [x] Validate command names and paths for security

## Phase 8: Example Commands and Templates ✓ COMPLETED
- [x] Create `_commands/help.mustache` - List available commands with front matter
- [x] Create `_commands/status.mustache` - System status information
- [x] Create `_commands/info/project.mustache` - Current project details
- [x] Create `_commands/info/agent.mustache` - Agent information
- [x] Create `_commands/create/collection.mustache` - Collection creation helper
- [x] Create `_commands/list/projects.mustache` - Project listing
- [x] Create `_commands/list/categories.mustache` - Category listing
- [x] Create `_commands/list/collections.mustache` - Collection listing
- [x] Integrate template rendering into command handler
- [x] Test all example commands with various argument patterns

## Phase 9: Integration Testing and TDD ✓ COMPLETED
- [x] Test command vs normal category routing
- [x] Verify no regression in existing guide functionality
- [x] Test complex command scenarios with arguments
- [x] Integration tests for command template rendering
- [x] End-to-end testing with real command execution
- [x] Performance testing with command discovery and execution

## Phase 10: Documentation and Polish ✓ COMPLETED
- [x] Document command system and argument syntax
- [x] Add command development best practices guide
- [x] Update guide prompt documentation
- [x] Create command template reference
- [x] Add debug logging for command execution
- [x] Final code quality checks and optimization

## Phase 11: Review Phase Enhancements ✓ COMPLETED
- [x] Create `:info/flags` command and menu system for feature flag display
- [x] Standardise formatting across all list commands for consistency
- [x] Add verbose mode to `:list/projects` with detailed category/collection display
- [x] Add instruction field support for action templates (enables commands to execute tools)
- [x] Update create commands with proper options and tool integration