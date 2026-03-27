# Change: Add Frontmatter To Exported Content

## Why

`export_content` currently exports rendered content without preserving the resolved content semantics that `mcp-guide` already understands at runtime.

That means exported files lose the collected document type, lose the resolved instruction override, and cannot tell a downstream agent whether the payload is user-facing information, agent-only information, or agent-only instruction content.

## What Changes

- Prepend exported payloads with YAML frontmatter containing the resolved `type` and `instruction`
- Resolve exported `type` across all collected documents using precedence:
  - `user/information`
  - `agent/information`
  - `agent/instruction`
- Resolve exported `instruction` using the existing multi-document instruction handling strategy so duplicates are removed and importance is preserved
- Update export/readback instructions so agents are told what the exported frontmatter fields mean and how to interpret them when reading exported files later

## Impact

**Affected specs:**
- `knowledge-export` - exported payloads gain resolved frontmatter metadata
- `content-tools` - export/readback instructions explain exported frontmatter semantics

**Affected code:**
- `src/mcp_guide/tools/tool_content.py` - compute resolved export metadata and prepend frontmatter
- `src/mcp_guide/templates/_system/_export.mustache` - explain exported frontmatter fields to agents
- Existing instruction/type resolution utilities reused by export flow
- Export-related unit and integration tests

**Benefits:**
- Exported files preserve the same behavioral semantics as in-memory content results
- Agents can safely re-consume exported documents without losing visibility rules
- Knowledge-indexed exports retain enough metadata to be interpreted correctly outside the immediate MCP response
