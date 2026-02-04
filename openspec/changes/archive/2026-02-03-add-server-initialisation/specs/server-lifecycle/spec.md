## ADDED Requirements

### Requirement: Server Initialisation Hook

The MCP Guide server SHALL provide a decorator-based mechanism for registering initialisation handlers that execute when the server starts.

#### Scenario: Register startup handler

- **WHEN** a module uses `@mcp.on_startup()` decorator on an async function
- **THEN** the function is registered as a startup handler
- **AND** the function executes when the server starts
- **AND** execution happens before any tool or prompt calls

#### Scenario: Multiple startup handlers

- **WHEN** multiple modules register startup handlers
- **THEN** all handlers execute in registration order
- **AND** failure in one handler does not prevent others from executing
- **AND** errors are logged but do not crash the server

#### Scenario: Handler execution timing

- **WHEN** the server starts via FastMCP lifespan hook
- **THEN** all registered startup handlers execute
- **AND** execution completes before the server accepts client connections
- **AND** handlers have access to server instance but not MCP Context

### Requirement: Startup Handler Registry

The GuideMCP class SHALL maintain a registry of startup handlers.

#### Scenario: Handler storage

- **WHEN** handlers are registered via decorator
- **THEN** they are stored in `_startup_handlers` list
- **AND** handlers are stored in registration order
- **AND** the same handler can be registered multiple times if needed

#### Scenario: Handler retrieval

- **WHEN** the lifespan hook needs to execute handlers
- **THEN** all registered handlers are accessible
- **AND** handlers are returned in registration order

### Requirement: Lifespan Integration

The server creation SHALL integrate startup handlers with FastMCP lifespan.

#### Scenario: Lifespan context manager

- **WHEN** the server is created
- **THEN** a lifespan context manager is provided to FastMCP
- **AND** the context manager executes all startup handlers on entry
- **AND** the context manager yields control to FastMCP
- **AND** the context manager supports future shutdown hooks on exit

#### Scenario: Error handling

- **WHEN** a startup handler raises an exception
- **THEN** the exception is caught and logged
- **AND** remaining handlers continue to execute
- **AND** the server continues to start

### Requirement: Backward Compatibility

The startup mechanism SHALL maintain compatibility with existing initialisation approaches.

#### Scenario: TIMER_ONCE events

- **WHEN** tasks use TIMER_ONCE events for initialisation
- **THEN** those events continue to work as before
- **AND** startup handlers can trigger task manager initialisation
- **AND** TIMER_ONCE provides fallback for tasks not using startup hooks

#### Scenario: on_tool initialisation

- **WHEN** tasks use on_tool() for initialisation
- **THEN** that mechanism continues to work
- **AND** startup handlers can call task_manager.on_tool()
- **AND** both approaches can coexist during migration
