# Deferred Tool Registration Pattern

## Problem

Current approach registers tools via decorators that execute **ON MODULE IMPORT**. This causes:

1. **Test contamination**: Python's module caching means tools stay registered with old server instances
2. **Complex workarounds**: Need `mcp_server_factory` fixture to reload modules
3. **Tight coupling**: Tool registration happens at import time, not when server is created
4. **Fragile tests**: Tests pass in isolation but fail in full suite due to import order

## Previous Solution (mcp-server-guide)

Reference: `../mcp-server-guide/src/mcp_server_guide/tool_registry.py`

Used a `register_tools()` function that wrapped tool functions **on demand**, not at import time. This allowed:
- Tools to be imported without side effects
- Registration to happen when server is initialized
- Clean separation between tool definition and registration

## Proposed Solution

### Lightweight Decorator Pattern

```python
# Registry to collect tool definitions
_tool_registry: dict[str, dict] = {}

def toolfunc(args_class: type[ToolArguments]):
    """Decorator that registers tool metadata without MCP registration.

    Stores tool function and args class in registry for later registration.
    """
    def decorator(func):
        # Store in registry (no MCP registration yet)
        _tool_registry[func.__name__] = {
            'func': func,
            'args_class': args_class,
        }

        # Return unwrapped function
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def register_tools(mcp_server):
    """Register all collected tools with the MCP server.

    Called explicitly during server initialization.
    Iterates registry and performs actual MCP registration.
    """
    for tool_name, metadata in _tool_registry.items():
        func = metadata['func']
        args_class = metadata['args_class']

        # Now do the actual MCP registration
        mcp_server.tool(args_class)(func)
```

### Usage Pattern

```python
# Tool definition (import-time, no side effects)
@toolfunc(CategoryListArgs)
async def category_list(args: CategoryListArgs, ctx: Context) -> str:
    """List categories."""
    # Implementation...


# Server initialization (explicit registration)
def create_server():
    mcp = FastMCP("mcp-guide")

    # Import tool modules (no registration happens)
    from mcp_guide.tools import tool_category, tool_collection

    # Explicitly register all tools
    register_tools(mcp)

    return mcp
```

## Benefits

1. **No test contamination**: Imports don't cause registration
2. **Simpler tests**: No need for module reloading fixtures
3. **Explicit control**: Registration happens when you want it
4. **Better separation**: Tool definition vs registration are separate concerns
5. **Easier debugging**: Clear point where registration occurs

## Why Not ToolArguments?

Initial idea was to use `ToolArguments` class for registration, but:
- `ToolArguments` is about JSON-structured arguments to tools
- Registration is about the tools themselves
- Mixing concerns violates single responsibility principle

## Implementation Notes

- Could use `ContextVar` to store registry per-context if needed
- Registry could be module-level dict (simplest approach)
- `register_tools()` would be called in `create_server()`
- Existing `@tools.tool()` decorator would be replaced with `@toolfunc()`

## Migration Path

1. Implement `toolfunc` decorator and `register_tools()` function
2. Update one tool module as proof of concept
3. Verify tests work without `mcp_server_factory` fixture
4. Migrate remaining tools
5. Remove workaround fixtures and documentation

## Related Files

- Current workaround: `tests/integration/conftest.py` (`mcp_server_factory`)
- Current workaround docs: `tests/integration/README.md`
- Current decorator: `src/mcp_core/tool_decorator.py` (`ExtMcpToolDecorator`)
- Reference implementation: `../mcp-server-guide/src/mcp_server_guide/tool_registry.py`

## Status

**IDEA** - Not yet implemented. Captured for future consideration after observing test complexity with current approach.

## Date

2025-12-07
