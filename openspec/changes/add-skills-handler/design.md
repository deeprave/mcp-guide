## Context

Guide URLs expose curated project content, while agents use distinct local skill conventions. The command must bridge those systems without making one agent's output appear valid for another.

## Goals / Non-Goals

**Goals:**
- Resolve supported Guide URL content into a project-scoped, agent-native skill.
- Make the command discoverable and fail before writing when the URL or agent is unsupported.

**Non-Goals:**
- Managing global user skills or synchronising existing skills.
- Defining a new cross-agent skill format.

## Decisions

- Use a command template to collect the URL and delegate retrieval and writing through existing Guide tools; this preserves MCP permissions and content semantics.
- Maintain agent-specific skill metadata and destination rules in one mapping; alternatives that infer paths from prompt prefixes would conflate unrelated capabilities.
- Generate a deterministic skill name from the URL and reject collisions unless explicit overwrite behavior is later designed.

## Risks / Trade-offs

- [Agent formats diverge] → isolate format rendering behind the agent mapping and test each supported agent.
- [A URL resolves to unsuitable content] → validate URL type and render only supported content resources.
