## Why

Guide URL content is accessible through MCP resources, but agents cannot directly turn that content into reusable, project-scoped skills. This prevents agent-specific workflows from using the same curated guidance in their native skill format.

## What Changes

- Add a command that creates a skill from a Guide URL for the current project.
- Render the generated skill in the format and installation location required by the detected agent.
- Reject or explain unsupported Guide URLs and agents without creating partial skill files.

## Capabilities

### New Capabilities

- `guide-url-skills`: Create agent-specific, project-scoped skills from Guide URL content.

### Modified Capabilities

- `tool-infrastructure`: Expose the skill-creation command through the command discovery and invocation pipeline.

## Impact

- Command templates and rendering context.
- Agent detection, agent-specific installation metadata, and skill output paths.
- Documentation and tests for supported agent formats and invalid inputs.
