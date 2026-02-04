# Implementation Tasks

**Approval gate**: APPROVED

## Phase 1: Deferred Registration Pattern

### 1.1 Create deferred registration infrastructure
- [x] Add `@toolfunc()` decorator that stores metadata without MCP registration
- [x] Add `@promptfunc()` decorator for prompts
- [x] Add `@resourcefunc()` decorator for resources
- [x] Create registry data structures using dict[str, ToolRegistration] pattern with registration tracking
- [x] Implement `register_tools(mcp)` function with idempotent registration
- [x] Implement `register_prompts(mcp)` function with idempotent registration
- [x] Implement `register_resources(mcp)` function with idempotent registration
- [x] Add consistent TRACE/DEBUG/ERROR logging to all registration functions (tools, prompts, resources)
- [x] Preserve all current functionality: prefixing, validation error handling, on_tool callback

### 1.2 Convert existing tools to deferred pattern
- [x] Convert tool_category.py to use `@toolfunc()`
- [x] Convert tool_collection.py to use `@toolfunc()`
- [x] Convert tool_content.py to use `@toolfunc()`
- [x] Convert tool_example.py to use `@toolfunc()`
- [x] Convert tool_feature_flags.py to use `@toolfunc()`
- [x] Convert tool_filesystem.py to use `@toolfunc()`
- [x] Convert tool_project.py to use `@toolfunc()`
- [x] Convert tool_utility.py to use `@toolfunc()`

### 1.3 Update server initialization
- [x] Update server.py to call `register_tools(mcp)` during init
- [x] Update server.py to call `register_prompts(mcp)` during init
- [x] Update server.py to call `register_resources(mcp)` during init
- [x] Remove conditional example tool import bloat

### 1.4 Update tests
- [x] Update `mcp_server_factory` for deferred registration pattern
- [x] Update tool registration tests
- [x] Verify no test contamination

## Phase 2: Discovery Tools

### 2.1 Implement list_tools
- [x] Create `list_tools` tool that queries tool registry
- [x] Return tool names, descriptions, and argument schemas
- [x] Follow Result pattern

### 2.2 Implement list_prompts
- [x] Create `list_prompts` tool that queries prompt registry
- [x] Return prompt names and descriptions
- [x] Follow Result pattern

### 2.3 Implement list_resources
- [x] Create `list_resources` tool that queries resource registry
- [x] Return resource URI patterns and descriptions
- [x] Follow Result pattern

### 2.4 Add tests
- [x] Test list_tools returns all registered tools
- [x] Test list_prompts returns registered prompts
- [x] Test list_resources returns registered resources
- [x] Integration tests for discovery tools

## Phase 3: Documentation
- [x] Add README.md documenting deferred registration pattern for AI consumption
