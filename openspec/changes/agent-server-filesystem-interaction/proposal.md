# Agent-Server Filesystem Interaction

**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium

## Why

MCP servers currently lack direct access to the agent's filesystem, creating significant challenges for interactive, file-based workflows. This limitation affects:

1. **Discovery**: Servers cannot discover files in project directories (e.g., `openspec/changes/`, `.adr/`)
2. **Content Access**: Servers cannot read file contents from the agent's environment
3. **State Synchronization**: Project state between agent and server cannot be synchronized
4. **Interactive Workflows**: File-based workflows are limited to passive document instructions rather than active, interactive operations

Current approaches are unreliable:
- Document instructions are static and not interactive
- Agent proactively following prompts is unreliable and non-deterministic
- Server-side file access doesn't work in all deployment scenarios (containers, remote servers)

This limitation prevents the MCP server from providing intelligent, context-aware assistance for file-based operations like OpenSpec change management, ADR tracking, and template rendering.

## What Changes

This change introduces a secure, bidirectional filesystem interaction pattern using MCP's sampling/completion request capability combined with explicit tool-based caching.

### New Components

1. **Filesystem Interaction Module** (`src/mcp_guide/filesystem/`)
   - Core sampling-based file operations
   - Path validation and security fencing
   - File content caching mechanism

2. **Path Security System** (`src/mcp_guide/filesystem/security.py`)
   - Path fencing to restrict access to allowed directories
   - Validation logic for file operations
   - Security policy configuration

3. **File Cache Manager** (`src/mcp_guide/filesystem/cache.py`)
   - Server-side file content caching
   - Cache invalidation strategies
   - Memory-efficient cache storage

4. **New MCP Tools**
   - `guide_cache_file` - Agent provides file content for server caching
   - `guide_list_directory` - Request directory listing from agent
   - `guide_read_file` - Request file content from agent

### Modified Components

1. **OpenSpec Tools** (`src/mcp_guide/tools/openspec/`)
   - Integrate filesystem interaction for change discovery
   - Use cached file contents for validation
   - Enable interactive file-based workflows

2. **Resource Handlers**
   - Update resource providers to use filesystem interaction
   - Cache frequently accessed files
   - Improve performance for file-based resources

### Configuration Changes

1. **Security Configuration**
   - Define allowed filesystem paths in project configuration
   - Default allowed paths: `openspec/`, `.adr/`, `specs/`, `templates/`
   - Per-project path customization

## Technical Approach

### Architecture

The solution uses MCP's sampling capability to create a request-response pattern:

1. **Server initiates request** using `ctx.request_sampling()`
2. **Agent processes request** and responds with file operations
3. **Agent caches results** using new `guide_cache_file` tool
4. **Server accesses cached data** for processing

### Security Model

Path fencing restricts file access to explicitly allowed directories:
- Paths are validated before any operation
- Relative paths are resolved and normalized
- Parent directory traversal (`../`) is blocked outside allowed paths
- Symbolic links are validated to prevent escape

### Performance Considerations

- File contents are cached to minimize sampling round-trips
- Cache invalidation based on file modification time
- Batch operations for multiple file requests
- Configurable cache size limits

## Success Criteria

1. **Functional Requirements**
   - Server can discover files in allowed directories
   - Server can read file contents through agent
   - File operations respect security boundaries
   - Cache performs efficiently with minimal memory overhead

2. **Security Requirements**
   - Path traversal attacks are prevented
   - Access outside allowed directories is blocked
   - All file operations are auditable

3. **Performance Requirements**
   - Directory listing completes in <2 seconds
   - File caching reduces redundant reads by >90%
   - Memory usage stays within reasonable limits (<50MB for typical projects)

4. **Integration Requirements**
   - OpenSpec tools successfully use filesystem interaction
   - Resources leverage cached file contents
   - Error handling provides clear feedback to agent and user
