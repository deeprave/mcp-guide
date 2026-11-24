## Why

Guide-served skills can be read through MCP, but agents cannot yet install one selected skill into the current project for clients that discover local skill directories. A command-guided export keeps that filesystem mutation under the agent's authority while making the source, destination, and selection explicit.

## What Changes

- Add a templated `skills/export` command, addressable as `guide://_skills/export/<skill-name>?force=true`.
- Have the command instruct the agent to export one named skill available to the current bound project, never to a global or another project's skill directory.
- Always export to `.agents/skills/<skill-name>`; do not offer another export destination.
- When `.claude` exists, create `.claude/skills` as needed and link an absent Claude skill entry to the canonical export. Preserve a non-matching existing Claude skill or link, and warn that Claude will use it instead.
- Render the available skill catalogue and overwrite requirements dynamically from the current session and parsed command arguments.
- Provide a bound `export_skill` tool that returns the complete rendered package as MIME documents, including local skill frontmatter and per-member permissions; the client agent remains responsible for local writes.
- When the skill name is omitted, direct the agent to choose one skill through an available client mechanism or a clear non-interactive fallback. Existing exports require `force=true` after explicit user confirmation.

## Capabilities

### New Capabilities
- `project-skill-export`: Export selected Guide skills into the current project's local skill directory through a rendered command.

### Modified Capabilities
- None. The existing Guide command URI routing and parsed keyword-argument contract already serves command templates.

## Impact

- Adds a packaged command template and supporting rendering context for the current project.
- Extends command-facing documentation and tests for single-skill selection, forced replacement, Claude compatibility links, and non-interactive clients.
- Does not add a server-side file-writing API: the rendered command tells the client agent how to create the selected local files. Exported files are user-owned snapshots of the current rendered session state and may be modified independently of Guide.
