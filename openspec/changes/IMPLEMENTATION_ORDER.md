# Implementation Order and Dependencies

> **⚠️ MAINTENANCE REQUIRED**: Update this file when:
> - Creating new change proposals (add dependencies)
> - Completing changes (mark complete, unblock dependents)
> - Archiving changes (remove from active list)
>
> **See also:** [ROADMAP.md](./ROADMAP.md) for high-level phases and detailed tool groups

This document tracks dependencies between OpenSpec change proposals to ensure correct implementation order.

---

## Required Implementation Sequence

### Phase 1: Foundation (mcp_core)

#### 1. logging-implementation
**Status:** Proposed
**ADR:** 004-logging-architecture
**Requires:** None
**Blocks:** tool-conventions (requires TRACE logging)

**Deliverables:**
- TRACE logging level in mcp_core
- File logging with WatchedFileHandler
- JSON and text formatters with redaction
- mcp_guide integration

**Validation:**
- ✅ TRACE level registered and functional
- ✅ File logging works on Unix/Linux
- ✅ Logger hierarchy prevents duplication
- ✅ All tests pass (>80% coverage)

---

### Phase 2: Tool Infrastructure

#### 2. tool-conventions
**Status:** Proposed
**ADR:** 005-tool-definition-conventions
**Requires:** logging-implementation (uses TRACE level for tool logging)
**Blocks:** All tool implementations (Phase 3)

**Deliverables:**
- ExtMcpToolDecorator with automatic logging
- Result[T] pattern with instruction field
- Base Pydantic model for tool arguments
- Explicit use pattern with Literal types

**Validation:**
- ✅ Decorator supports prefix configuration
- ✅ Automatic TRACE logging on tool calls
- ✅ Result[T] with instruction field works
- ✅ Example tool demonstrates all patterns

---

### Phase 3: Tool Implementations

**Note:** All Phase 3 groups require tool-conventions. Phase 3a should be implemented first as it provides foundational operations. Other groups (3b, 3c, 3d) can proceed in parallel after 3a.

#### 3a. guide-content-tools (IMPLEMENT FIRST)
**Status:** Not Started
**Requires:** tool-conventions
**Priority:** HIGH - Foundational

**Tools:**
- Category operations (get/add/update/remove/list)
- Collection operations (get/add/update/remove/list)
- Document operations (create/get/update/delete/list)
- Content access (get_category_content, get_file_content, search_content)

**Implementation Order:**
1. Category operations (foundation)
2. Collection operations (depends on categories)
3. Document operations (depends on categories)
4. Content access (uses all above)

**Validation:**
- ✅ All CRUD operations working
- ✅ Explicit use pattern on destructive operations
- ✅ Content retrieval efficient
- ✅ Search functional

#### 3b. guide-project-tools
**Status:** Not Started
**Requires:** tool-conventions
**Can Start After:** guide-content-tools (recommended, not required)

**Tools:**
- get_current_project
- switch_project
- clone_project
- get_project_config
- set_project_config
- set_project_config_values

**Validation:**
- ✅ Project switching works
- ✅ Configuration persistence
- ✅ Clone preserves settings

#### 3c. guide-utilities-tools
**Status:** Not Started
**Requires:** tool-conventions
**Can Start After:** tool-conventions (no other dependencies)

**Tools:**
- get_agent_info

**Validation:**
- ✅ Agent info captured correctly

#### 3d. mcp-discovery-tools
**Status:** Not Started
**Requires:** tool-conventions
**Can Start After:** tool-conventions (no other dependencies)

**Tools:**
- list_tools
- list_prompts
- list_resources (possibly)

**Validation:**
- ✅ Complete enumeration
- ✅ Useful metadata included

---

## Dependency Graph

```
Phase 1: Foundation
    logging-implementation (ADR-004)
        ↓
Phase 2: Infrastructure
    tool-conventions (ADR-005)
        ↓
Phase 3: Tool Implementations
    ├─→ guide-content-tools (3a) ← IMPLEMENT FIRST
    ├─→ guide-project-tools (3b) ← Can parallel after 3a
    ├─→ guide-utilities-tools (3c) ← Can parallel after tool-conventions
    └─→ mcp-discovery-tools (3d) ← Can parallel after tool-conventions
```

---

## Key Dependencies Explained

### logging-implementation → tool-conventions
**Reason:** ExtMcpToolDecorator uses `logger.trace()` for automatic tool invocation logging
**Impact:** Cannot implement tool conventions without TRACE level
**Validation:** Verify TRACE level available and functional before starting tool-conventions

### tool-conventions → All tool implementations
**Reason:** All tools must use ExtMcpToolDecorator, Result[T] pattern, and follow ADR-005
**Impact:** Inconsistent tool behavior without conventions
**Validation:** Verify decorator and Result pattern available before implementing any tools

### guide-content-tools → Other tool groups (recommended)
**Reason:** Content operations are foundational - other tools may need to access/manipulate content
**Impact:** Other tools may need refactoring if content operations change
**Validation:** Complete guide-content-tools before starting other groups (recommended, not required)

---

## Parallel Work Opportunities

### After Phase 1 (logging-implementation)
- Documentation for mcp_core logging
- Integration tests for logging in mcp_guide
- Research third-party redaction packages

### After Phase 2 (tool-conventions)
- Multiple tool groups can proceed in parallel
- Recommend completing guide-content-tools first
- guide-utilities-tools and mcp-discovery-tools fully independent

### Within Phase 3a (guide-content-tools)
- Must implement sequentially: categories → collections → documents → content access
- Cannot parallelize due to dependencies

---

## Success Criteria Per Phase

### Phase 1: logging-implementation
- ✅ TRACE level registered and functional
- ✅ mcp_log.py in mcp_core with all required functions
- ✅ mcp_log_filter.py stub with get_redaction_function()
- ✅ WatchedFileHandler for Unix/Linux file logging
- ✅ JSON and text formatters with redaction integration
- ✅ mcp_guide integrated with logging (config + main.py)
- ✅ All tests pass (>80% coverage)
- ✅ Documentation complete

### Phase 2: tool-conventions
- ✅ ExtMcpToolDecorator implemented with prefix support
- ✅ Automatic TRACE logging integrated into decorator
- ✅ Result[T] pattern with instruction field
- ✅ Base Pydantic model for tool arguments
- ✅ Explicit use pattern with Literal types
- ✅ Pydantic validation integration
- ✅ All tests pass
- ✅ ADR-005 published
- ✅ Tool implementation guide available

### Phase 3: Tool Implementations
- ✅ Each tool uses ExtMcpToolDecorator
- ✅ Each tool returns Result[T]
- ✅ Destructive tools use explicit use pattern
- ✅ Tool descriptions include auto-generated schema
- ✅ Tests verify conventions followed
- ✅ Integration tests cover workflows

---

## Notes

- **Breaking Changes**: tool-conventions may require updates to ADR-003 if instruction field not present
- **Testing Strategy**: Integration tests should verify end-to-end flow from tool call → logging → Result return
- **Documentation**: All tool documentation must use undecorated names per ADR-005
- **Maintenance**: Update this file and ROADMAP.md when creating, completing, or archiving changes
