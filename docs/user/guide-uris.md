# Guide URIs

mcp-guide exposes content through the `guide://` URI scheme. This gives AI agents a universal way to access your project's content, commands, and configuration — regardless of what MCP features the agent supports.

## Why Guide URIs?

The `guide://` URI scheme is the canonical way to refer to mcp-guide content and commands. Some clients also support equivalent prompt syntax, but not all agents support MCP prompts or resources natively.

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

These work exactly like the equivalent prompt expressions — the same expressions, the same results.

## Command URIs

Commands use an underscore prefix to distinguish them from content:

| URI | What It Does |
|-----|--------------|
| `guide://_status` | Current project status |
| `guide://_project` | Project information |
| `guide://_help` | List available commands |
| `guide://_flags/project/list` | List project flags |
| `guide://_export/list` | List tracked exports |

Command URIs mirror the prompt command syntax — for example, a prompt-style `:status` request becomes `guide://_status`.

### Command Arguments

Commands can accept positional arguments via path segments and keyword arguments via query parameters:

```
guide://_help/flags              # Positional: help for the "flags" command
guide://_flags/project/set/workflow?value=true   # Positional + keyword arguments
```

When a command argument is an absolute filesystem path, the URI will contain a double slash before the path value. For example, `guide://_project/perm/read/add//external/data` uses the first slash to separate the command from its first positional argument, and the second slash is the leading `/` of the absolute path itself.

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
