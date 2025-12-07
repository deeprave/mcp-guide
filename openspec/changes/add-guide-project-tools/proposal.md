# Change: Add Guide Project Management Tools

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**Jira**: GUIDE-110

## Why

Project management tools enable switching between projects, cloning configurations, and accessing project information. These tools are essential for multi-project workflows.

Currently, project switching happens implicitly through context detection. Users need explicit project management capabilities to:
- Switch between projects without changing directories
- Inspect project configurations without loading them
- Clone project configurations for reuse
- List all available projects

## What Changes

Implement five project management tools:

1. **`get_current_project`** - Returns current project information (verbose/non-verbose)
2. **`set_current_project`** - Switches to project by name (creates if needed)
3. **`clone_project`** - Copies project configuration with merge/replace options
4. **`list_projects`** - Lists all available projects (verbose/non-verbose)
5. **`list_project`** - Gets specific project details by name

All tools:
- Return Result pattern responses (ADR-003)
- Follow tool conventions (ADR-008)
- Self-documenting via MCP schema
- Include comprehensive error handling

## Impact

- **Affected specs**: New capability `guide-project-tools`
- **Affected code**: New tools module (`tool_project.py`), project management
- **Dependencies**: Result pattern (ADR-003), tool conventions (ADR-008), session management, ConfigManager
- **Breaking changes**: None (new tools only)
- **Test coverage**: >90% required
