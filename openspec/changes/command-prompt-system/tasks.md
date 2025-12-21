# Command-Based Prompt System - Implementation Tasks

## Phase 1: Category Name Validation
- [ ] Add validation to prevent user categories starting with `_`
- [ ] Update category creation tools to reject underscore prefixes
- [ ] Add validation to existing category management functions
- [ ] Test category name validation with various underscore patterns
- [ ] Update error messages for invalid category names

## Phase 2: Command Prefix Detection and Path Transformation
- [ ] Add command prefix detection (`:` and `;`) to guide prompt parsing
- [ ] Implement path transformation from `:command/sub` to `_commands/command/sub`
- [ ] Add command path validation (no wildcards, security checks)
- [ ] Test prefix detection and path transformation logic
- [ ] Handle edge cases (empty commands, malformed paths)

## Phase 3: Advanced Argument Parsing
- [ ] Implement argument parser for `--flag`, `--no-flag`, `--key=value` formats
- [ ] Add support for `key=value` pairs without dashes
- [ ] Separate positional arguments from flag/key arguments
- [ ] Build kwargs and args template context structure
- [ ] Test complex argument parsing scenarios

## Phase 4: Integration with get_content Engine
- [ ] Modify guide prompt to route commands through get_content
- [ ] Ensure `_commands` directory is treated as virtual category
- [ ] Add auto-extension logic (append `.*` for file discovery)
- [ ] Test command execution through existing content pipeline
- [ ] Verify template rendering works with command context

## Phase 5: Template Context Enhancement
- [ ] Add `kwargs` and `args` to template context for commands
- [ ] Ensure command templates receive full standard context
- [ ] Test argument access in command templates
- [ ] Verify context precedence and override behavior
- [ ] Add command metadata to context if needed

## Phase 6: File Discovery and Auto-Extension
- [ ] Implement auto-extension logic for command files
- [ ] Support multiple template extensions in `_commands`
- [ ] Test file discovery with various command file types
- [ ] Handle missing command files with clear errors
- [ ] Optimize file discovery performance for commands

## Phase 7: Error Handling and Edge Cases
- [ ] Handle missing command files through get_content error system
- [ ] Add validation for command path security (no directory traversal)
- [ ] Test malformed argument parsing edge cases
- [ ] Handle template errors in command execution
- [ ] Add comprehensive error messages for command issues

## Phase 8: Integration Testing and Validation
- [ ] Test command vs normal category routing
- [ ] Verify no regression in existing guide functionality
- [ ] Test complex command scenarios with arguments
- [ ] Integration tests for command template rendering
- [ ] Performance testing with command execution

## Phase 9: Example Commands and Documentation
- [ ] Create example command templates (help, status, create/category)
- [ ] Test example commands with various argument patterns
- [ ] Document command system and argument syntax
- [ ] Add command development best practices
- [ ] Update guide prompt documentation

## Phase 10: Polish and Optimization
- [ ] Optimize argument parsing performance
- [ ] Add debug logging for command execution
- [ ] Implement command template validation
- [ ] Final testing and quality assurance
- [ ] Code review and cleanup
