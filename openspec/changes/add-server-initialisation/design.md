# Design: Server Initialisation Hook

## Context

MCP Guide needs a reliable server initialisation mechanism that:
- Executes before any tool calls
- Works across all MCP clients
- Decouples initialisation from task manager implementation
- Allows multiple initialisation handlers

FastMCP provides a `lifespan` parameter that accepts an async context manager for startup/shutdown hooks.

## Goals

- Provide decorator-based registration pattern consistent with `@mcp.tool()`, `@mcp.resource()`
- Execute all registered handlers during server startup
- Maintain backward compatibility with existing TIMER_ONCE approach
- Keep initialisation logic decoupled from specific implementations

## Non-Goals

- Replace existing task manager event system
- Provide shutdown hooks (can be added later if needed)
- Support conditional initialisation based on client type

## Decisions

### 1. Decorator Pattern

Use `@mcp.on_startup()` decorator to register initialisation handlers:

```python
@mcp.on_startup()
async def initialise_tasks():
    """Initialise task manager on startup."""
    task_manager = get_task_manager()
    await task_manager.on_tool()
```

**Rationale:**
- Consistent with existing `@mcp.tool()`, `@mcp.resource()` patterns
- Declarative and easy to understand
- Allows multiple handlers to be registered independently
- Decoupled from implementation details

**Alternatives considered:**
- Direct lifespan function: Less flexible, couples all initialisation together
- Configuration-based: More complex, less discoverable

### 2. Handler Registry

Store handlers in `GuideMCP._startup_handlers: list[Callable]`:

```python
class GuideMCP(FastMCP):
    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        self.agent_info: Optional["AgentInfo"] = None
        self._startup_handlers: list[Callable[[], Awaitable[None]]] = []

    def on_startup(self) -> Callable:
        """Decorator to register startup handlers."""
        def decorator(func: Callable[[], Awaitable[None]]) -> Callable:
            self._startup_handlers.append(func)
            return func
        return decorator
```

**Rationale:**
- Simple list storage
- Handlers execute in registration order
- Easy to test and debug

### 3. Lifespan Implementation

Create lifespan context manager in `server.py`:

```python
@asynccontextmanager
async def guide_lifespan(server: GuideMCP) -> AsyncIterator[dict]:
    """Lifespan hook for server initialisation and shutdown."""
    # Startup: Execute all registered handlers
    for handler in server._startup_handlers:
        try:
            await handler()
        except Exception as e:
            logger.error(f"Startup handler {handler.__name__} failed: {e}")

    yield {}  # Server runs

    # Shutdown: cleanup if needed (future)
```

Pass to GuideMCP:

```python
mcp = GuideMCP(
    name=server_name,
    instructions="...",
    lifespan=guide_lifespan
)
```

**Rationale:**
- Uses FastMCP's built-in lifespan support
- Errors in one handler don't prevent others from running
- Logging for debugging
- Extensible for shutdown hooks later

### 4. Backward Compatibility

Keep existing TIMER_ONCE mechanism as fallback:
- Startup handlers trigger task manager initialisation
- TIMER_ONCE events still work for tasks that need them
- Gradual migration path

## Implementation Order

1. Add handler registry to GuideMCP
2. Implement decorator
3. Create lifespan function
4. Wire into server creation
5. Migrate existing initialisation code
6. Add tests

## Risks & Mitigations

**Risk:** Handler failures prevent server startup
**Mitigation:** Catch exceptions, log errors, continue with other handlers

**Risk:** Handlers depend on each other
**Mitigation:** Document that handlers should be independent; execution order is registration order

**Risk:** Handlers need MCP Context
**Mitigation:** Document that startup runs before any client requests; use alternative approaches (task manager, global state)

## Open Questions

None - design is straightforward and well-supported by FastMCP.
