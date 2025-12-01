# ADR 009: Client Project Name Detection

## Status

ACCEPTED

## Context

MCP servers need to determine the client's current working directory/project to provide context-aware functionality. Without explicit configuration, servers must infer the project name from available information sources.

### The Problem

- **Server CWD ≠ Client CWD**: The server process runs in its own directory, which has no relationship to the client's working directory
- **No Guaranteed Context**: Not all MCP clients provide project/workspace information
- **Multiple Possible Sources**: Project name can come from various sources with different reliability levels

### MCP Specification: Client Roots

According to the [MCP Specification (Draft) - Client Roots](https://modelcontextprotocol.io/specification/draft/client/roots):

#### What are Roots?

- **Definition**: URIs representing locations the client wants the server to pay attention to
- **Primary Use**: Filesystem boundaries defining where servers can operate
- **Format**: MUST be `file://` URIs in current specification
- **Structure**: `{ "uri": "file:///path/to/project", "name": "Optional Display Name" }`

#### Client Capabilities

Clients that support roots MUST declare capability during initialization:

```json
{
  "capabilities": {
    "roots": {
      "listChanged": true
    }
  }
}
```

- `listChanged`: Whether client will emit notifications when roots change

#### Accessing Roots

**Server-initiated request:**

```python
# Server sends roots/list request to client
result = await ctx.session.list_roots()
# Returns: ListRootsResult with array of Root objects
```

**Request/Response:**

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "roots/list"
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "roots": [
      {
        "uri": "file:///home/user/projects/myproject",
        "name": "My Project"
      }
    ]
  }
}
```

#### Change Notifications

When roots change, clients with `listChanged` capability MUST send:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/roots/list_changed"
}
```

#### Error Handling

**Client doesn't support roots:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Roots not supported"
  }
}
```

### When Roots Are NOT Available

Based on research and real-world issues:

1. **Client doesn't implement roots capability**
   - Error code: `-32601` (Method not found)
   - Example: Some MCP clients don't support roots at all
   - See: [Cursor Forum - MCP client does not support roots/list](https://forum.cursor.com/t/mcp-client-does-not-support-roots-list/77248)

2. **Client advertises capability but doesn't implement**
   - Client sends `roots` capability in initialization
   - But `roots/list` request fails or returns empty
   - See: [Claude Code Issue #3315](https://github.com/anthropics/claude-code/issues/3315)

3. **Roots not configured by user**
   - Client supports roots but user hasn't configured workspace
   - Returns empty array: `{ "roots": [] }`

4. **Context not available**
   - Tool called without request context (e.g., in tests)
   - `ctx` parameter is `None`

### FastMCP Implementation Details

#### Context Object

```python
from mcp.server.fastmcp import Context

@tools.tool()
async def my_tool(ctx: Context) -> str:
    # Context provides access to session
    session = ctx.session  # Returns ServerSession instance

    # Session can request roots from client
    roots_result = await session.list_roots()
    # Returns: types.ListRootsResult
```

#### Context Structure

- **Context**: FastMCP wrapper providing clean interface
  - `ctx.session`: Access to underlying `ServerSession`
  - `ctx.request_context`: Access to full `RequestContext`
  - Automatically injected by FastMCP when parameter is type-hinted

- **ServerSession**: MCP protocol session
  - `session.list_roots()`: Async method to request roots from client
  - Returns `types.ListRootsResult` with `roots: list[Root]`
  - Can raise exceptions if client doesn't support roots

#### When Context is Available

- **Tool execution**: Context is injected for every tool call
- **Prompt execution**: Context available in prompt handlers
- **Resource handlers**: Context available when reading resources
- **NOT available**: Outside request handlers (e.g., server initialization, tests without mocking)

### Environment Variable: PWD

**What is PWD?**

- Standard Unix environment variable containing current working directory
- Set by shell when process starts
- Represents the directory where the client process was launched

**Reliability Issues:**

1. **May not be set**: Some environments don't set PWD
2. **May be relative**: Could be ".", "..", or other relative path
3. **May be stale**: If process changed directory, PWD might not update
4. **Client vs Server**: PWD reflects where MCP client was launched, not server

**When PWD is Useful:**

- Client launched from project directory
- PWD contains absolute path
- No other context available

**Validation Required:**

```python
pwd = os.environ.get("PWD")
if pwd:
    pwd_path = Path(pwd)
    # MUST validate it's absolute
    if pwd_path.is_absolute():
        # Can use pwd_path.name as project name
```

## Decision

### Project Name Detection Priority

We will detect project name using the following priority order:

1. **PRIMARY: Client Roots** (via MCP Context)
   - Request `ctx.session.list_roots()` if context available
   - Extract first root URI
   - Parse `file://` URI to get absolute path
   - Use basename as project name
   - Cache the result

2. **SECONDARY: Cached Project Name**
   - If previously detected from roots
   - Avoids repeated requests to client
   - Updated when roots change notification received

3. **LAST FALLBACK: PWD Environment Variable**
   - Only if context unavailable or roots request fails
   - MUST validate it's an absolute path
   - Reject relative paths: ".", "..", "./foo", etc.
   - Use basename as project name
   - Cache the result

4. **ERROR: Cannot Determine**
   - Return error with instruction
   - Message: "Project context not available. Call switch_project with the basename of the current working directory."

### Implementation Requirements

#### All Tools Must Accept Context

```python
from mcp.server.fastmcp import Context

@tools.tool(CategoryListArgs)
async def category_list(ctx: Context) -> str:
    """List all categories in the current project."""
    try:
        session = get_current_session(ctx)
    except ValueError as e:
        result = Result.failure(str(e), error_type="no_project")
        result.instruction = "Call switch_project with your project name"
        return result.to_json_str()

    # ... rest of implementation
```

#### Session Lazy-Loading

```python
def get_current_session(ctx: Optional[Context] = None) -> Session:
    """Get or lazy-create current session.

    Args:
        ctx: Optional MCP Context for accessing client roots

    Returns:
        Session instance

    Raises:
        ValueError: If project name cannot be determined
    """
    # Check ContextVar for existing session
    sessions = active_sessions.get({})
    if sessions:
        return next(iter(sessions.values()))

    # Lazy-create session
    project_name = _determine_project_name(ctx)

    config_manager = ConfigManager()
    session = Session(config_manager=config_manager, project_name=project_name)

    # Store in ContextVar for subsequent calls
    set_current_session(session)

    return session
```

#### Project Name Detection

```python
async def _determine_project_name(ctx: Optional[Context] = None) -> str:
    """Determine project name with correct priority.

    Priority:
    1. Client roots (via Context) - PRIMARY
    2. Cached project name (from previous detection)
    3. PWD environment variable - LAST FALLBACK (validated)

    Args:
        ctx: Optional MCP Context for accessing client roots

    Returns:
        Project name (basename of project directory)

    Raises:
        ValueError: With instruction on how to fix
    """
    global _cached_project_name

    # Priority 1: Try client roots (PRIMARY)
    if ctx is not None:
        try:
            roots_result = await ctx.session.list_roots()
            if roots_result.roots:
                first_root = roots_result.roots[0]
                if first_root.uri.startswith("file://"):
                    from urllib.parse import urlparse
                    parsed = urlparse(str(first_root.uri))
                    project_path = Path(parsed.path)
                    if project_path.is_absolute():
                        project_name = project_path.name
                        _cached_project_name = project_name  # Cache it
                        return project_name
        except Exception as e:
            # Client may not support list_roots
            # Log and continue to fallbacks
            logger.debug(f"Failed to get roots from client: {e}")

    # Priority 2: Use cached project name
    if _cached_project_name:
        return _cached_project_name

    # Priority 3: PWD as LAST FALLBACK
    pwd = os.environ.get("PWD")
    if pwd:
        pwd_path = Path(pwd)
        # MUST be absolute path, reject relative paths
        if pwd_path.is_absolute():
            project_name = pwd_path.name
            _cached_project_name = project_name  # Cache it
            return project_name

    # Cannot determine project
    raise ValueError(
        "Project context not available. "
        "Call switch_project with the basename of the current working directory."
    )
```

### Prohibited Practices

1. **NEVER use `os.getcwd()`**
   - Returns server's current directory
   - Has no relationship to client's working directory
   - Will give incorrect results

2. **NEVER accept relative paths from PWD**
   - "." is not a valid project name
   - ".." is not a valid project name
   - "./foo" is not a valid project name
   - Only absolute paths are acceptable

3. **NEVER assume roots are available**
   - Always handle `-32601` error (method not found)
   - Always handle empty roots array
   - Always have fallback strategy

## Consequences

### Positive

- ✅ Follows MCP specification for client roots
- ✅ Graceful degradation when roots unavailable
- ✅ Clear error messages with fix instructions
- ✅ Caching reduces repeated client requests
- ✅ Works across different MCP client implementations
- ✅ Testable with mock Context

### Negative

- ⚠️ Requires all tools to accept Context parameter
- ⚠️ Async complexity for project name detection
- ⚠️ May fail if client doesn't support roots AND PWD is invalid
- ⚠️ Caching requires invalidation strategy for root changes

### Neutral

- 📝 Need to handle root change notifications (future enhancement)
- 📝 May want to support multiple roots (future enhancement)
- 📝 Could add user preference for project selection (future enhancement)

## References

- [MCP Specification - Client Roots](https://modelcontextprotocol.io/specification/draft/client/roots)
- [WorkOS - Understanding Roots in MCP](https://workos.com/blog/mcp-roots-guide)
- [Cursor Forum - MCP client does not support roots/list](https://forum.cursor.com/t/mcp-client-does-not-support-roots-list/77248)
- [Claude Code Issue #3315 - roots capability advertised but not implemented](https://github.com/anthropics/claude-code/issues/3315)
- [VS Code Issue #272420 - programmatically registered MCP server don't get roots](https://github.com/microsoft/vscode/issues/272420)
- FastMCP Source: `mcp/server/fastmcp/server.py` - Context class
- MCP Source: `mcp/server/session.py` - ServerSession.list_roots()

## Notes

- This ADR supersedes any previous assumptions about session initialization
- Implementation plan: `.todo/session-lazy-loading-implementation-plan.md`
- Related to mcp-server-guide pattern but adapted for mcp-guide structure
