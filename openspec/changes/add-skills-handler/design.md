## Context

Guide URLs expose curated project content, while agents use distinct local skill conventions. Guide needs to make a complete skill package available directly to an agent, rather than treating a skill as one rendered file or assuming a local skill path exists.

## Goals / Non-Goals

**Goals:**
- Maintain a canonical, project-aware skill package containing `SKILL.md` and optional `references/`, `scripts/`, and `assets/` members.
- Let an agent discover skills through Guide, inspect frontmatter and usage guidance, and read individual package members on demand.
- Support optional import and agent-native filesystem export without making either the canonical representation.
- Make unsupported packages, URLs, agents, and collisions fail before any output is written.

**Non-Goals:**
- Managing global user skills or synchronising existing skills.
- Building the MCP v2 engine migration as part of this change.
- Providing server-side script execution; agents retrieve and execute package scripts in their own workspace.

## Decisions

- Treat a filesystem-compatible package layout as canonical: `SKILL.md` is the entrypoint, with optional supporting directories. This preserves lossless import/export while allowing Guide to serve the same package virtually.
- Provide a skills catalog resource and member resources such as `guide://skills/<skill-id>/SKILL.md`. Catalog entries expose the metadata and use guidance required for an agent to select a skill.
- Render package content against the current project and Guide settings when it is served. Export materialises that resolved package only when an agent requires filesystem discovery.
- Maintain agent-specific export metadata and destination rules in one mapping; alternatives that infer paths from prompt prefixes would conflate unrelated capabilities.
- The `upgrade-mcp-version` change owns the v2 migration. After it lands, use v2 discovery instructions and resource capabilities as the preferred direct-serving bridge, with legacy behaviour retained only where necessary for compatible clients.
- Generate deterministic skill names and reject collisions unless explicit overwrite behaviour is later designed.

## Risks / Trade-offs

- [Agent formats diverge] → keep exports behind the agent mapping; the canonical package remains filesystem-compatible.
- [A package contains executable scripts] → expose them as readable members; the agent materialises or runs them, and Guide does not execute them.
- [MCP v2 rollout timing] → do not couple the engine refactor to skills; keep the direct-serving bridge sequenced after `upgrade-mcp-version`.
