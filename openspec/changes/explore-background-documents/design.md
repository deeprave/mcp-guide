# Design: Background document imports

## Architecture

```
Main Agent                    Background Agent              MCP Server
    |                              |                            |
    |-- determine imports -------->|                            |
    |   (paths, category, meta)    |                            |
    |                              |-- fs_read(path) ---------> |
    |   (continues working)        |<-- content ----------------|
    |                              |-- send_file_content ------>|
    |                              |   (category, name, content)|
    |                              |                            |-- DocumentTask
    |                              |                            |   (store)
    |                              |-- fs_read(next path) ----->|
    |                              |   ...repeat...             |
    |                              |                            |
    |<-- completion/status --------|                            |
```

The main agent is unblocked immediately after delegation. The background agent handles the sequential I/O loop. The MCP server receives `send_file_content` calls identically regardless of which agent sends them.

## Option A: Natural language delegation

The simplest approach. The main agent composes a plain text task description and hands it to the platform's background mechanism.

Example task:
```
Import the following files into category "docs":
- /path/to/file1.md (name: file1.md, type: agent/information)
- /path/to/file2.md (name: file2.md, type: agent/information)

For each file:
1. Read the file using fs_read
2. Call send_file_content with category="docs", the file content, and the specified name and type
```

Pros:
- Works with any agent that supports background/delegation
- No mcp-guide changes required
- Easy to test manually

Cons:
- LLM interprets the task each time — slight variability in execution
- No structured validation of the task description
- Main agent must compose the task description itself

## Option B: Command template generates delegation task

mcp-guide provides a `:document/import` command that accepts parameters and renders a structured, optimised task description.

```
:document/import docs /path/to/file1.md /path/to/file2.md --type=agent/information
```

Renders a delegation-ready task description that the agent passes to its background mechanism.

Pros:
- Consistent, well-structured task descriptions
- Server can validate category exists, check for obvious issues before delegation
- Reduces main agent's composition burden

Cons:
- Adds a command to mcp-guide
- Still relies on agent-side delegation mechanism
- Template output needs to work across different agent platforms

## Option C: Dedicated import tool with delegation hint

A `document_import` tool that accepts a manifest (list of paths + metadata) and returns a delegation-ready task. The tool itself doesn't do the I/O — it validates inputs and returns structured instructions.

```python
document_import(category="docs", files=[
    {"path": "/path/to/file1.md", "type": "agent/information"},
    {"path": "/path/to/file2.md", "type": "agent/information"},
])
# Returns: structured task description for delegation
```

Pros:
- Full server-side validation before delegation starts
- Structured input/output
- Could include progress tracking hooks

Cons:
- New tool registration
- More complex than a command template
- Still can't do the actual I/O server-side

## Agent platform capabilities

### kiro-cli
- `delegate` tool: async background agents sharing same tools and permissions
- Status checking via `delegate` with status operation
- One task per agent at a time

### Claude Code
- Background task capability (details TBD)
- Likely similar tool sharing model

### Codex
- Background capability (details TBD)

### Other agents
- Capability varies; natural language delegation (Option A) is the universal fallback

## Error handling considerations

- File not found: background agent reports failure, but main agent may have moved on
- Category doesn't exist: can be validated before delegation (Options B/C)
- Store collision: DocumentTask already handles upsert, so this is not an error
- Partial failure: some files imported, some failed — need a summary mechanism
- Timeout: background agent may be killed before completing all imports

## Feedback mechanisms

- kiro-cli: `delegate` status check returns output when complete
- Polling: main agent periodically checks delegation status
- Store query: main agent can verify imports by listing documents in the category
- Event-based: DocumentTask could emit completion events (future enhancement)

## Evaluation criteria

- Time savings vs sequential import (target: >50% reduction for 3+ files)
- Reliability across agent platforms
- Error visibility — can the user tell what succeeded/failed?
- Complexity cost — is the implementation worth the savings?
