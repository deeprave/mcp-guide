## Why

Guide URL content is accessible through MCP resources, but Guide cannot present reusable skills as complete, discoverable packages. Agents therefore cannot use centralised, project-aware skills directly through Guide, and filesystem exports become stale copies rather than a bridge to a canonical skill source.

## What Changes

- Represent skills as packages with `SKILL.md` plus optional references, scripts, and assets.
- Serve a project-aware virtual skill catalog and package members through Guide resources, including the frontmatter and usage guidance agents need to select a skill.
- Allow agents to retrieve package scripts through Guide and execute their content in their own workspace.
- Provide import and agent-native filesystem export as optional adapters to the canonical Guide package.
- Sequence the direct agent-serving bridge after the MCP v2 engine migration, where discovery instructions and resource capabilities provide a stronger protocol integration.

## Capabilities

### New Capabilities

- `guide-url-skills`: Serve and exchange project-aware Guide skill packages.

### Modified Capabilities

- `tool-infrastructure`: Expose skill package discovery and optional import/export commands through the normal command pipeline.

## Impact

- Resource discovery and rendering context.
- Agent detection, agent-specific installation metadata, and skill output paths.
- The forthcoming `upgrade-mcp-version` change, which remains responsible for the MCP v2 engine migration itself.
- Documentation and tests for package layouts, supported agents, and invalid inputs.
