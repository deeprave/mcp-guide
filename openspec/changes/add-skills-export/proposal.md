## Why

Guide-served skills can be read through MCP, but agents cannot yet install a selected set into the current project for clients that discover local skill directories. A command-guided export keeps that filesystem mutation under the agent's authority while making the source, destination, and selection explicit.

## What Changes

- Add a templated `skills/export` command, addressable as `guide://_skills/export/<destination>?skills=<comma-separated-names>`.
- Have the command instruct the agent to export only skills available to the current bound project, never to a global or another project's skill directory.
- Default an omitted destination to `.agents`; allow an explicitly supplied relative destination and an agent-specific skill location selected by the user.
- Render the available skill catalogue and destination requirements dynamically from the current session and parsed command arguments.
- When the client exposes a choice or confirmation mechanism, direct the agent to use it to choose the destination, multi-select omitted skills, and confirm the final export; retain a clear non-interactive fallback.

## Capabilities

### New Capabilities
- `project-skill-export`: Export selected Guide skills into the current project's local skill directory through a rendered command.

### Modified Capabilities
- None. The existing Guide command URI routing and parsed keyword-argument contract already serves command templates.

## Impact

- Adds a packaged command template and supporting rendering context for the current project and current agent.
- Extends command-facing documentation and tests for explicit destinations, selection, confirmation, and non-interactive clients.
- Does not add a server-side file-writing API: the rendered command tells the client agent how to create the selected local files.
