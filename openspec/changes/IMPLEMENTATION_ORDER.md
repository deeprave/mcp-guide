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
**Status:** ✅ Complete (Ready for archive)
**ADR:** 004-logging-architecture
**JIRA:** GUIDE-2
**Epic:** GUIDE-24
**Completed:** 2025-11-27
**Requires:** None
**Unblocks:** tool-conventions

**Deliverables:**
- ✅ TRACE logging level in mcp_core (92% coverage)
- ✅ File logging with WatchedFileHandler
- ✅ JSON and text formatters with redaction
- ✅ mcp_guide integration (31 tests passing)

**Validation:**
- ✅ TRACE level registered and functional
- ✅ File logging works on Unix/Linux
- ✅ Logger hierarchy prevents duplication
- ✅ All tests pass (>80% coverage achieved)

---

### Phase 2: Tool Infrastructure

#### 2. tool-conventions
**Status:** Proposed
**ADR:** 008-tool-definition-conventions
**Requires:** ✅ logging-implementation (Complete)
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

**Note:** All Phase 3 changes require tool-conventions. Implement in the order listed below due to dependencies.

#### 3a. add-category-tools (IMPLEMENT FIRST)
**Status:** Proposed
**Requires:** tool-conventions
**Blocks:** add-collection-tools, add-content-tools
**Priority:** HIGH - Configuration management foundation

**Tools:**
- `category_add(name, dir?, description?, patterns?)` - Create category
- `category_remove(name)` - Delete category (auto-removes from collections)
- `category_change(name, new_name?, dir?, description?, patterns?)` - Replace config
- `category_update(name, add_patterns?, remove_patterns?)` - Modify incrementally

**Features:**
- Comprehensive validation (name, dir, description, patterns)
- Traversal prevention and path safety
- Auto-update collections on remove/rename
- Change vs update semantics

**Validation:**
- ✅ All CRUD operations working
- ✅ Validation prevents unsafe operations
- ✅ Auto-update collections works
- ✅ Configuration persistence safe

#### 3b. add-collection-tools
**Status:** Proposed
**Requires:** tool-conventions, add-category-tools
**Blocks:** add-content-tools
**Priority:** HIGH - Configuration management

**Tools:**
- `collection_add(name, description?, categories?)` - Create collection
- `collection_remove(name)` - Delete collection
- `collection_change(name, new_name?, description?, categories?)` - Replace config
- `collection_update(name, add_categories?, remove_categories?)` - Modify incrementally

**Features:**
- Category reference validation (referential integrity)
- Change vs update semantics
- Comprehensive validation

**Validation:**
- ✅ All CRUD operations working
- ✅ Category references validated
- ✅ Configuration persistence safe
- ✅ Integration with category tools

#### 3c. add-content-tools
**Status:** Proposed
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Blocks:** add-guide-uri-scheme
**Priority:** HIGH - Content retrieval

**Tools:**
- `get_content(category_or_collection, pattern?)` - Unified content access
- `get_category_content(category, pattern?)` - Category-specific retrieval
- `get_collection_content(collection, pattern?)` - Collection-specific retrieval

**Features:**
- Result pattern with error instructions
- Pattern matching (glob syntax)
- Single match → plain markdown
- Multiple matches → MIME multipart
- Agent-friendly error handling

**Validation:**
- ✅ All three tools implemented
- ✅ Pattern matching works
- ✅ MIME multipart formatting correct
- ✅ Result pattern with instructions
- ✅ Integration tests pass

#### 3d. add-guide-uri-scheme
**Status:** Proposed
**Requires:** tool-conventions, add-content-tools
**Priority:** MEDIUM - Resource layer

**Features:**
- MCP `resources/list` handler with guide:// URIs
- MCP `resources/read` handler for URI resolution
- URI patterns: help, collection/{id}, category/{name}, category/{name}/{docId}, document/{context}/{docId}
- Delegates to content tools for retrieval

**Validation:**
- ✅ Resources list returns templates
- ✅ URI parsing works correctly
- ✅ Content delegation functional
- ✅ guide://help provides documentation

#### 3e. add-guide-project-tools (Placeholder)
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Priority:** MEDIUM - Project management

**Tools:**
- get_current_project - Returns all data about current project
- set_current_project - Sets current project by name, creating if required
- clone_project - Copy existing project to current or new project

**Validation:**
- TBD when detailed proposal created

#### 3f. add-guide-utility-tools (Placeholder)
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Priority:** LOW - Utilities

**Tools:**
- get_agent_info - Returns information about agent/client

**Validation:**
- TBD when detailed proposal created

#### 3g. add-mcp-discovery-tools (Placeholder)
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Priority:** LOW - Introspection

**Tools:**
- list_prompts - Enumerate available prompts
- list_resources - Enumerate available resources
- list_tools - Enumerate available tools

**Validation:**
- TBD when detailed proposal created
- ✅ Content delegation functional
- ✅ guide://help provides documentation

---

## Dependency Graph

```
Phase 1: Foundation
    ✅ logging-implementation (ADR-004) - COMPLETE
        ↓
Phase 2: Infrastructure
    tool-conventions (ADR-008)
        ↓
Phase 3: Tool Implementations
    add-category-tools (3a) ← IMPLEMENT FIRST
        ↓
    add-collection-tools (3b)
        ↓
    add-content-tools (3c)
        ↓
    add-guide-uri-scheme (3d)

    Placeholders (depend on category + collection):
    ├─→ add-guide-project-tools (3e)
    ├─→ add-guide-utility-tools (3f)
    └─→ add-mcp-discovery-tools (3g)
```

**Implementation Order:**
1. ✅ logging-implementation (Complete)
2. tool-conventions (Ready to start)
3. add-category-tools (After tool-conventions)
4. add-collection-tools (After add-category-tools)
5. add-content-tools (After add-collection-tools)
6. add-guide-uri-scheme (After add-content-tools)
7. Placeholders (After add-category-tools + add-collection-tools)

---

## Key Dependencies Explained

### ✅ logging-implementation → tool-conventions (COMPLETE)
**Reason:** ExtMcpToolDecorator uses `logger.trace()` for automatic tool invocation logging
**Impact:** Cannot implement tool conventions without TRACE level
**Status:** Unblocked - logging-implementation complete

### tool-conventions → All tool implementations
**Reason:** All tools must use ExtMcpToolDecorator, Result[T] pattern, and follow ADR-008
**Impact:** Inconsistent tool behavior without conventions
**Validation:** Verify decorator and Result pattern available before implementing any tools

### add-content-tools → add-guide-uri-scheme
**Reason:** URI scheme delegates to content tools for actual retrieval
**Impact:** Cannot implement resources without content retrieval
**Validation:** Complete add-content-tools before starting add-guide-uri-scheme

### add-category-tools → add-collection-tools
**Reason:** Collections reference categories and need validation
**Impact:** Cannot validate category references without category tools
**Validation:** Complete add-category-tools before starting add-collection-tools

---

## Parallel Work Opportunities

### ✅ After Phase 1 (logging-implementation) - COMPLETE
- Documentation for mcp_core logging ✅
- Integration tests for logging in mcp_guide ✅
- Ready to start Phase 2

### After Phase 2 (tool-conventions)
- Only add-category-tools can start (no other dependencies)
- All other tools must wait for category and/or collection tools

### Sequential Implementation Required
- **add-category-tools** → **add-collection-tools** → **add-content-tools** → **add-guide-uri-scheme**
- No parallelization possible due to dependencies
- Placeholders (project/utility/discovery) can start after category + collection complete

### Within Changes
- **add-category-tools**: Four tools can be implemented in parallel (share validation)
- **add-collection-tools**: Four tools can be implemented in parallel (share validation)
- **add-content-tools**: Three tools can be implemented in parallel (independent)
- **add-guide-uri-scheme**: Sequential (URI parsing → resource handlers → help content)

---

## Success Criteria Per Phase

### Phase 1: logging-implementation ✅ COMPLETE
- ✅ TRACE level registered and functional
- ✅ mcp_log.py in mcp_core with all required functions (92% coverage)
- ✅ mcp_log_filter.py stub with get_redaction_function() (100% coverage)
- ✅ WatchedFileHandler for Unix/Linux file logging
- ✅ JSON and text formatters with redaction integration
- ✅ mcp_guide integrated with logging (config + main.py)
- ✅ All tests pass (31 tests, >80% coverage)
- ✅ Documentation complete

### Phase 2: tool-conventions
- ✅ ExtMcpToolDecorator implemented with prefix support
- ✅ Automatic TRACE logging integrated into decorator
- ✅ Result[T] pattern with instruction field
- ✅ Base Pydantic model for tool arguments
- ✅ Explicit use pattern with Literal types
- ✅ Pydantic validation integration
- ✅ All tests pass
- ✅ ADR-008 published
- ✅ Tool implementation guide available

### Phase 3: Tool Implementations
- ✅ Each tool uses ExtMcpToolDecorator
- ✅ Each tool returns Result[T] with instruction field
- ✅ Destructive tools use explicit use pattern (if applicable)
- ✅ Tool descriptions include auto-generated schema
- ✅ Tests verify conventions followed
- ✅ Integration tests cover workflows
- ✅ Validation prevents unsafe operations (category/collection tools)
- ✅ Content formatting correct (single vs multiple matches)

---

## Notes

- **Breaking Changes**: tool-conventions may require updates to ADR-003 if instruction field not present
- **Testing Strategy**: Integration tests should verify end-to-end flow from tool call → logging → Result return
- **Documentation**: All tool documentation must use undecorated names per ADR-008
- **Maintenance**: Update this file and ROADMAP.md when creating, completing, or archiving changes
