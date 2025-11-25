# Implementation Order and Dependencies

## Required Implementation Sequence

The following changes must be implemented in this specific order due to dependencies:

### Phase 1: Development Environment
**1. python-dev-environment** (No dependencies)
- Sets up Python 3.13+ project structure
- Installs all dependencies (FastMCP, Pydantic, testing tools)
- Configures dev tools (pytest, ruff, mypy, pre-commit)
- Copies templates and osvcheck.py
- Establishes build system with uv_build
- Must be completed first - nothing can be built without this

### Phase 2: Server Foundation
**2. main-entry-point** (Depends on: python-dev-environment)
- Creates main entry point with asyncio
- Implements FastMCP server initialization
- Sets up STDIO transport (MVP)
- Configures console script entry point
- Provides minimal working MCP server
- Cannot start until dependencies are installed

### Phase 3: Core Architecture
**3. config-session-management** (Depends on: main-entry-point)
- Implements ProjectConfigManager (singleton)
- Implements GuideSession (non-singleton)
- Sets up ContextVar for session tracking
- Creates immutable Project model
- Establishes configuration management patterns
- Requires working server to integrate with
- **Status**: PLACEHOLDER - to be fleshed out after Phase 2

## Dependency Graph

```
python-dev-environment
    ↓
main-entry-point
    ↓
config-session-management (placeholder)
    ↓
[Future: Tool implementations]
```

## Key Dependencies

### Phase 1 → Phase 2
- **Build System**: uv_build must be configured
- **Dependencies**: FastMCP, Pydantic, Click must be installed
- **Dev Tools**: pytest, mypy, ruff must be available
- **Package Structure**: src/mcp_core/ and src/mcp_guide/ must exist

### Phase 2 → Phase 3
- **Server Instance**: FastMCP server must be creatable
- **Entry Point**: main() and async_main() must work
- **Testing Infrastructure**: MCP Inspector integration must work
- **Console Script**: mcp-guide command must be available

### Phase 3 → Future Tools
- **Configuration**: ProjectConfigManager must be available
- **Session Management**: GuideSession must be creatable
- **ContextVar**: Session tracking must work
- **Models**: Immutable Project model must exist

## Shared Code Dependencies

### From python-dev-environment
- `src/mcp_core/result.py` - Result[T] pattern (ADR-003)
- `src/mcp_core/mcp_log.py` - Logging module (ADR-004)
- `src/mcp_core/exceptions.py` - Core exceptions
- `templates/` - Mustache templates for content generation

### From main-entry-point
- `src/mcp_guide/main.py` - Entry point and transport modes
- `src/mcp_guide/server.py` - Server creation and initialization

### From config-session-management
- `src/mcp_guide/config.py` - ProjectConfigManager
- `src/mcp_guide/session.py` - GuideSession
- `src/mcp_guide/models.py` - Pydantic models

## Implementation Notes

### Phase 1: Foundation First
- **Critical**: Nothing can proceed without dev environment
- **Validation**: Must pass all pre-commit hooks before moving on
- **Testing**: Basic pytest infrastructure must work

### Phase 2: Minimal Server
- **Goal**: Get a working MCP server that responds to handshake
- **Validation**: Must work with MCP Inspector
- **Testing**: Integration tests with mcp-inspector required

### Phase 3: Architecture
- **Goal**: Establish core patterns for all future tools
- **Validation**: Must support concurrent sessions
- **Testing**: Unit tests for config/session management

## Parallel Work Opportunities

None at this stage - each phase must complete before the next begins due to tight coupling.

Future phases (after Phase 3) may allow parallel tool development.

## Blocking Issues

- **Phase 1**: None - can start immediately
- **Phase 2**: Blocked until Phase 1 complete
- **Phase 3**: Blocked until Phase 2 complete and validated

## Success Criteria Per Phase

### Phase 1 Complete When:
- [ ] All dependencies installed via uv
- [ ] All dev tools configured and working
- [ ] `uv build` succeeds
- [ ] Pre-commit hooks pass
- [ ] Templates copied and renamed

### Phase 2 Complete When:
- [ ] `mcp-guide` command starts server
- [ ] Server responds to MCP handshake
- [ ] MCP Inspector can connect
- [ ] All tests pass (unit + integration)
- [ ] Type checking and linting pass

### Phase 3 Complete When:
- [ ] ProjectConfigManager can load/save configs
- [ ] GuideSession can be created per project
- [ ] ContextVar tracks sessions correctly
- [ ] Concurrent sessions work
- [ ] All tests pass with ≥90% coverage
