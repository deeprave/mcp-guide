# Implementation Tasks

## 1. Core Infrastructure

- [ ] 1.1 Add startup handler registry to GuideMCP class
- [ ] 1.2 Implement `@mcp.on_startup()` decorator
- [ ] 1.3 Create lifespan context manager function
- [ ] 1.4 Wire lifespan to GuideMCP initialisation in create_server()

## 2. Integration

- [ ] 2.1 Update ClientContextTask to use @mcp.on_startup()
- [ ] 2.2 Update WorkflowMonitorTask to use @mcp.on_startup()
- [ ] 2.3 Update OpenSpecTask to use @mcp.on_startup()

## 3. Testing

- [ ] 3.1 Add unit tests for startup handler registration
- [ ] 3.2 Add unit tests for lifespan execution
- [ ] 3.3 Add integration test for multiple handlers
- [ ] 3.4 Verify existing TIMER_ONCE behaviour still works

## 4. Documentation

- [ ] 4.1 Document @mcp.on_startup() decorator usage
- [ ] 4.2 Add example to tool implementation guide
- [ ] 4.3 Update architecture documentation
