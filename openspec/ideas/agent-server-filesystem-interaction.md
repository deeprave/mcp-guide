# Idea: Agent-Server File System Interaction Pattern

**Status:** Future Consideration
**Priority:** Post-MVP
**Created:** 2025-11-25

## Problem

MCP servers don't have direct access to the agent's filesystem, creating challenges for:
- Discovering files in project directories (e.g., `openspec/changes/`)
- Reading file contents from the agent's environment
- Synchronizing project state between agent and server
- Providing interactive, file-based workflows

Current approaches rely on:
- Document instructions (not interactive)
- Agent proactively following prompts (unreliable)
- Server-side file access (not available in all deployment scenarios)

## Proposed Solution

Use MCP's **sampling/completion request** capability combined with **explicit tool-based caching** for reliable agent-server file system interaction.

### Architecture

```python
# Server requests agent to perform file operations
result = await ctx.request_sampling(
    messages=[{"role": "user", "content": "List all files in openspec/changes/"}],
    system_prompt="You are a file system assistant"
)

# Agent responds with file list
# Server can then request specific files

file_content = await ctx.request_sampling(
    messages=[{"role": "user", "content": f"Read file {file_path} and provide content"}]
)

# Agent provides content via tool call to cache
@mcp.tool()
async def guide_cache_file(path: str, content: str) -> Result[dict]:
    """Agent provides file content for server caching"""
    # Validate path is within allowed directories
    # Store in server-side cache
    # Return success
```

### Security: Path Fencing

Restrict file access to specific project directories:

```python
ALLOWED_PATHS = [
    "openspec/",
    ".adr/",
    "specs/",
    "templates/",
]

def is_path_allowed(path: str) -> bool:
    """Check if path is within allowed directories"""
    return any(path.startswith(allowed) for allowed in ALLOWED_PATHS)
```

### Workflow Example

1. **Discovery Phase**
   - Server requests: "List files in openspec/changes/"
   - Agent responds with file list
   - Server validates paths against allowed directories

2. **Content Phase**
   - Server requests specific files
   - Agent reads and provides content via tool calls
   - Server caches content for processing

3. **Processing Phase**
   - Server operates on cached file contents
   - Provides analysis, validation, or transformations
   - Returns results to agent

## Benefits

- **Explicit Control**: Server explicitly requests what it needs
- **Security**: Path fencing prevents unauthorized access
- **Reliability**: Sampling requests are more deterministic than prompt instructions
- **Flexibility**: Works regardless of server deployment (local, container, remote)
- **Interactive**: Enables back-and-forth file-based workflows

## Challenges

- **Sampling Support**: Not all MCP clients may support sampling requests
- **Performance**: Multiple round-trips for file operations
- **Caching Strategy**: Need efficient cache management
- **Error Handling**: Agent may fail to provide requested files

## Use Cases

1. **OpenSpec Integration**
   - Discover active changes in `openspec/changes/`
   - Read proposal and task files
   - Validate spec formatting
   - Track implementation progress

2. **ADR Management**
   - List ADRs in `openspec/adr/`
   - Read and index architectural decisions
   - Provide ADR search and reference tools

3. **Template Synchronization**
   - Discover available templates
   - Read template contents for rendering
   - Validate template syntax

4. **Project Analysis**
   - Scan project structure
   - Analyze file relationships
   - Generate project documentation

## Implementation Considerations

### Phase 1: Research
- Investigate MCP sampling/completion request capabilities
- Test with different MCP clients (Claude Desktop, Kiro CLI, etc.)
- Determine client support and limitations

### Phase 2: Prototype
- Implement basic file discovery via sampling
- Create path validation and fencing
- Build simple file caching mechanism

### Phase 3: Integration
- Integrate with OpenSpec workflow
- Add tools for file-based operations
- Provide prompts that leverage file access

### Phase 4: Enhancement
- Optimize caching strategy
- Add file watching/change detection
- Implement batch file operations

## Related Work

- MCP Protocol: Sampling/Completion Requests
- MCP Resources: Server-side file exposure
- Agent Tool Calling: Structured data exchange

## Next Steps

1. Research MCP sampling capabilities in detail
2. Test with available MCP clients
3. Create proof-of-concept implementation
4. Evaluate feasibility and performance
5. Consider as post-MVP enhancement

## Notes

This pattern could significantly enhance MCP server capabilities by bridging the gap between server logic and agent filesystem access. However, it requires careful security considerations and may not be universally supported across all MCP clients.

The key insight is using **sampling requests** as a bidirectional communication channel where the server can request specific actions from the agent, rather than relying on passive prompt instructions.
