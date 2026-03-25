# Exploration: Background document imports

**Status**: Exploration
**Priority**: Low
**Complexity**: Unknown

## Problem

Importing documents into the store is slow — typically 30s to a minute per document. The bottleneck is the LLM sitting in the data path as a dumb relay: it reads file content into its context window via `fs_read`, then copies it back out via `send_file_content`. The content is opaque payload that the LLM never needs to understand, analyse, or transform. This is an expensive round-trip through the most constrained resource in the pipeline.

For batch imports the problem compounds — each document is sequential: read → compose tool call → wait for response → next.

## Constraints

- The MCP server cannot read the agent's filesystem. The server may be running in Docker (stdio or HTTP transport), on a remote host, or otherwise isolated from the agent's filesystem. A server-side import tool only works when client and server share a filesystem, which is one configuration among many.
- MCP has no "pipe" or "tool chaining" primitive — there's no way to say "read this file and pass its content directly to this other tool call without the LLM seeing it." The LLM must mediate every tool-to-tool data transfer.
- The actual store operation is already async — `send_file_content` dispatches an `FS_FILE_CONTENT` event that `DocumentTask` handles. The store side is not the bottleneck.

## Approach: Agent-side delegation

Since the bottleneck is LLM mediation and we can't eliminate it, we can move it to a background agent:

1. Main agent determines what to import (file paths, URLs, category, metadata)
2. Main agent delegates the mechanical read → send loop to a background agent
3. Main agent continues with other work immediately
4. Background agent handles the sequential I/O without blocking the conversation

### Agent platform support

- kiro-cli: `delegate` tool — spawns async background agents that share the same tools and permissions
- Claude Code: background task capability
- Codex: background capability
- Other agents: likely to have equivalent mechanisms as the pattern matures

The task description is natural language — mcp-guide doesn't need to know how the agent backgrounds it.

### mcp-guide's role

mcp-guide could provide a command template (e.g. `:document/import`) that:
- Accepts a file list, category, and metadata parameters
- Renders a structured task description optimised for delegation
- The agent hands that description to whatever background mechanism it has

This keeps mcp-guide agent-agnostic — it composes the task, the agent handles execution.

## Open questions

- Is a command template the right abstraction, or is this purely a workflow pattern to document?
- Should the template generate agent-specific delegation syntax, or always natural language?
- How do we handle progress/completion feedback from the background agent?
- Can we batch multiple `send_file_content` calls in a single delegation task effectively?
- Is there a way to reduce LLM involvement further — e.g. agent frameworks that support "blind relay" tool calls where content bypasses the context window?
- How do we handle errors in the background (file not found, category doesn't exist, store collision)?

## Exploration plan

This should be explored on a separate git branch, not on main. Try different approaches:
1. Manual delegation with explicit task descriptions
2. Command template that generates delegation-ready instructions
3. Test across available agent platforms (kiro-cli delegate as first target)
4. Measure actual time savings vs current sequential approach
