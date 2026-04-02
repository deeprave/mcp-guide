# Guide URIs

mcp-guide exposes content through the `guide://` URI scheme. This gives AI agents a universal way to access your project's content, commands, and configuration — regardless of what MCP features the agent supports.

## Why Guide URIs?

The `@guide` prompt is the primary way most users interact with mcp-guide. But not all agents support MCP prompts or resources natively. Some agents (like Codex) only have access to tools.

Guide URIs solve this by providing a single, consistent interface that works everywhere:

- Agents with full MCP support can read `guide://` URIs directly as resources
- Agents with only tool support can use the `read_resource` tool to fetch the same URIs
- Commands that would normally require prompt support become accessible to any agent

## Content URIs

Content URIs retrieve documents from your categories and collections:

| URI | What It Does |
|-----|--------------|
| `guide://docs` | All documents in the `docs` category |
| `guide://docs/readme` | Documents matching `readme` pattern in `docs` |
| `guide://docs/workflow+tracking` | Documents matching both `workflow` AND `tracking` in `docs` |
| `guide://guidelines` | All content from the `guidelines` collection |

These work exactly like `@guide` prompt expressions — the same expressions, the same results.

## Command URIs

Commands use an underscore prefix to distinguish them from content:

| URI | What It Does |
|-----|--------------|
| `guide://_status` | Current project status |
| `guide://_project` | Project information |
| `guide://_help` | List available commands |
| `guide://_flags/project/list` | List project flags |
| `guide://_export/list` | List tracked exports |

Command URIs mirror the `@guide :command` syntax — `@guide :status` becomes `guide://_status`.

### Command Arguments

Commands can accept positional arguments via path segments and keyword arguments via query parameters:

```
guide://_help/flags              # Positional: help for the "flags" command
guide://_flags/project/set?name=workflow&value=true   # Keyword arguments
```

## Using `read_resource` as a Fallback

If your agent doesn't support reading MCP resources directly, you can use the `read_resource` tool to fetch any `guide://` URI:

```
read_resource("guide://docs")
read_resource("guide://_status")
read_resource("guide://_help/flags")
```

This is particularly useful for agents like Codex that interact primarily through tools. The content returned is identical — the tool is just a different way to reach it.

## Practical Examples

**Getting project context:**
```
guide://guidelines          # Load all project guidelines
guide://context/project     # Project-specific context
guide://lang/python         # Language-specific guides
```

**Running commands:**
```
guide://_status             # Check project and workflow state
guide://_project            # View categories, collections, permissions
guide://_check              # Run code quality checks
guide://_review             # Start a code review
guide://_commit             # Generate commit message guidance
```

**Managing content:**
```
guide://_export/list        # View tracked exports
guide://_document/list      # View stored documents
guide://_flags              # View feature flag status
```

## Next Steps

- **[Getting Started](getting-started.md)** — Basic concepts and first steps
- **[Commands](commands.md)** — Full command reference
- **[Stored Documents](stored-documents.md)** — Ingesting and managing documents
- **[Content Management](content-management.md)** — Categories, collections, and expressions
