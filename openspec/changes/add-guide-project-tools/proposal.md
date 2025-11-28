# Change: Add Guide Project Management Tools

## Why

Project management tools enable switching between projects, cloning configurations, and accessing project information. These tools are essential for multi-project workflows.

## What Changes

- Implement `get_current_project` tool (returns all data about current project)
- Implement `set_current_project` tool (sets current project by name, creating if required)
- Implement `clone_project` tool (copy existing project to current or new project)
- Return Result pattern responses
- Follow tool conventions (ADR-008)

## Impact

- Affected specs: New capability `guide-project-tools`
- Affected code: New tools module, project management
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008), category/collection tools
- Breaking changes: None (new tools)
