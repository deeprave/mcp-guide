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
**Unblocks:** tool-conventions, add-feature-flags

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

### Phase 2: Configuration and Infrastructure

#### 2. add-feature-flags
**Status:** 📋 Proposed (0% complete)
**Requires:** ✅ logging-implementation (Complete)
**Blocks:** template-support, add-openspec-support
**Priority:** HIGH - Required for advanced features

**Deliverables:**
- Feature flag data models (global and project-specific)
- MCP tools: list_flags, set_flag, get_flag
- Flag resolution hierarchy (project → global → None)
- Type-safe flag values (bool, str, list[str], dict[str, str])
- Configuration validation and persistence

**Validation:**
- ⏳ Feature flags stored in configuration models
- ⏳ MCP tools provide complete flag management
- ⏳ Resolution hierarchy works correctly
- ⏳ Immediate persistence on flag changes
- ⏳ Validation prevents invalid flag names/values

#### 3. tool-conventions
**Status:** 📋 Proposed (0% complete)
**ADR:** 008-tool-definition-conventions
**Requires:** ✅ logging-implementation (Complete)
**Blocks:** All tool implementations (Phase 3)

**Deliverables:**
- ExtMcpToolDecorator with automatic logging
- Result[T] pattern with instruction field
- Base Pydantic model for tool arguments
- Explicit use pattern with Literal types

**Validation:**
- ⏳ Decorator supports prefix configuration
- ⏳ Automatic TRACE logging on tool calls
- ⏳ Result[T] with instruction field works
- ⏳ Example tool demonstrates all patterns

---

### Phase 3: Tool Implementations

**Note:** All Phase 3 changes require tool-conventions. Implement in the order listed below due to dependencies.

#### 4a. add-category-tools
**Status:** ✅ Complete (2025-12-08)
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

#### 4b. add-collection-tools
**Status:** ✅ Complete (2025-12-08)
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

#### 4c. add-content-tools
**Status:** ✅ Complete (2025-12-08)
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

#### 4d. add-guide-uri-scheme
**Status:** 📋 Proposed (0% complete)
**Requires:** tool-conventions, add-content-tools
**Priority:** MEDIUM - Resource layer

**Features:**
- MCP `resources/list` handler with guide:// URIs
- MCP `resources/read` handler for URI resolution
- URI patterns: help, collection/{id}, category/{name}, category/{name}/{docId}, document/{context}/{docId}
- Delegates to content tools for retrieval

**Validation:**
- ⏳ Resources list returns templates
- ⏳ URI parsing works correctly
- ⏳ Content delegation functional
- ⏳ guide://help provides documentation

#### 4e. add-guide-project-tools
**Status:** ✅ Complete (2025-12-08)
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Priority:** MEDIUM - Project management

**Tools:**
- get_current_project - Returns all data about current project
- set_current_project - Sets current project by name, creating if required
- clone_project - Copy existing project to current or new project
- list_projects - List all available projects
- list_project - Get specific project details

**Validation:**
- ✅ All 5 tools implemented and tested
- ✅ 21 integration tests covering all workflows
- ✅ MCP tool documentation complete
- ✅ 641 tests passing, 90% coverage

#### 4f. add-guide-utility-tools
**Status:** 📋 Proposed (0% complete)
**Requires:** tool-conventions
**Priority:** LOW - Utilities

**Tools:**
- get_agent_info - Returns information about agent/client

**Validation:**
- ⏳ Agent info captured correctly
- ⏳ Useful for debugging and logging

#### 4g. add-mcp-discovery-tools
**Status:** 📋 Proposed (0% complete)
**Requires:** tool-conventions
**Priority:** LOW - Introspection

**Tools:**
- list_prompts - Enumerate available prompts
- list_resources - Enumerate available resources
- list_tools - Enumerate available tools

**Validation:**
- ⏳ Complete tool/prompt/resource enumeration
- ⏳ Useful metadata included
- ⏳ Helps agents discover capabilities

#### 4h. tool-descriptions
**Status:** ✅ Complete (2025-12-20)
**Requires:** tool-conventions
**Priority:** HIGH - Documentation standards

**Features:**
- 4-section documentation format for tools and prompts
- Field description completeness for Pydantic models
- 50-character first line guideline for docstrings
- Reference comments linking to documentation templates

**Validation:**
- ✅ Tools README template with 4-section format created
- ✅ Prompts README template with varargs handling created
- ✅ All Field descriptions added to tool argument models
- ✅ Tool docstrings follow 50-character guideline
- ✅ Reference comments added to all modules
- ✅ Specification updated with new requirements

#### 4i. collections-with-patterns
**Status:** 📋 Proposed (0% complete)
**Requires:** add-collection-tools
**Priority:** LOW - Enhancement

**Features:**
- Allow collections to override category patterns
- Per-collection pattern customization
- Backward compatibility with existing collections

**Validation:**
- ⏳ Collections can specify custom patterns
- ⏳ Pattern override works correctly
- ⏳ Existing collections unaffected

---

### Phase 4: Advanced Features

#### 5a. template-support
**Status:** 📋 Proposed (0% complete)
**Requires:** add-feature-flags
**Blocks:** add-openspec-support
**Priority:** HIGH - Template rendering system

**Features:**
- Mustache/Chevron template rendering
- TemplateContext with ChainMap hierarchy
- Template discovery and rendering pipeline
- Integration with feature flags for conditional rendering

**Validation:**
- ⏳ Template discovery works
- ⏳ Context hierarchy resolves correctly
- ⏳ Chevron rendering functional
- ⏳ Feature flag integration complete

#### 5b. add-openspec-support
**Status:** 📋 Proposed (0% complete)
**Requires:** add-feature-flags, template-support
**Priority:** MEDIUM - OpenSpec workflow integration

**Features:**
- Conditional OpenSpec detection via feature flags
- MCP tools for OpenSpec workflows
- MCP resources for OpenSpec project state
- Template context integration

**Validation:**
- ⏳ Feature flag conditional activation
- ⏳ OpenSpec workflow tools functional
- ⏳ Template integration complete
- ⏳ MCP resources queryable

#### 5c. hook-uri-templates
**Status:** 📋 Proposed (0% complete)
**Requires:** add-guide-uri-scheme, template-support, add-feature-flags
**Priority:** MEDIUM - Dynamic hook content support

**Features:**
- Template-enabled hook instructions via URI references
- Dynamic content based on workflow mode and feature flags
- Agent-followable guide:// URIs with template variables
- Context-aware guidance and instructions

**Validation:**
- ⏳ Hook scripts output URI instructions with template variables
- ⏳ Agents resolve template variables in guide:// URIs
- ⏳ Template content supports feature flags and context variables
- ⏳ Backward compatibility with existing static hook scripts

---

## Dependency Graph

```
Phase 1: Foundation
    ✅ logging-implementation (ADR-004) - COMPLETE
        ↓
Phase 2: Configuration and Infrastructure
    📋 add-feature-flags (NEW)
    📋 tool-conventions (ADR-008)
        ↓
Phase 3: Tool Implementations
    ✅ add-category-tools (4a) - COMPLETE
        ↓
    ✅ add-collection-tools (4b) - COMPLETE
        ↓
    ✅ add-content-tools (4c) - COMPLETE
        ↓
    📋 add-guide-uri-scheme (4d) - READY TO START

    Parallel (depend on tool-conventions only):
    ✅ add-guide-project-tools (4e) - COMPLETE
    📋 add-guide-utility-tools (4f)
    📋 add-mcp-discovery-tools (4g)
    📋 collections-with-patterns (4h) - depends on add-collection-tools

Phase 4: Advanced Features
    📋 template-support (5a) ← depends on add-feature-flags
        ↓
    📋 add-openspec-support (5b) ← depends on add-feature-flags + template-support
    📋 hook-uri-templates (5c) ← depends on add-guide-uri-scheme + template-support + add-feature-flags
```

**Critical Path:**
1. ✅ logging-implementation (Complete)
2. 📋 add-feature-flags (NEW - blocks advanced features)
3. 📋 tool-conventions (blocks remaining tools)
4. 📋 template-support (after add-feature-flags)
5. 📋 add-openspec-support (after template-support)
6. 📋 hook-uri-templates (after add-guide-uri-scheme + template-support + add-feature-flags)

---

## Key Dependencies Explained

### ✅ logging-implementation → add-feature-flags, tool-conventions (COMPLETE)
**Reason:** Both use logging infrastructure for tool operations and validation
**Impact:** Cannot implement configuration tools or conventions without logging
**Status:** Unblocked - logging-implementation complete

### add-feature-flags → template-support, add-openspec-support
**Reason:** Both features require feature flag conditional activation
**Impact:** Cannot implement advanced features without feature flag system
**Validation:** Feature flag resolution and MCP tools must work before proceeding

### template-support → add-openspec-support
**Reason:** OpenSpec integration uses template context hierarchy
**Impact:** Cannot integrate OpenSpec data without template system
**Validation:** Template rendering and context resolution must work

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
- Both add-feature-flags and tool-conventions can start
- Documentation for mcp_core logging ✅
- Integration tests for logging in mcp_guide ✅

### After Phase 2 (add-feature-flags, tool-conventions)
- **Sequential**: add-category-tools → add-collection-tools → add-content-tools → add-guide-uri-scheme
- **Parallel**: add-guide-utility-tools, add-mcp-discovery-tools can start after tool-conventions
- **Advanced**: template-support can start after add-feature-flags

### Within Changes
- **add-category-tools**: Four tools can be implemented in parallel (share validation) ✅
- **add-collection-tools**: Four tools can be implemented in parallel (share validation) ✅
- **add-content-tools**: Three tools can be implemented in parallel (independent) ✅
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

### Phase 2: Configuration and Infrastructure

#### add-feature-flags
- ⏳ Feature flag data models in configuration
- ⏳ MCP tools: list_flags, set_flag, get_flag functional
- ⏳ Resolution hierarchy (project → global → None) works
- ⏳ Type validation for flag values
- ⏳ Immediate persistence on flag changes
- ⏳ All tests pass

#### tool-conventions
- ⏳ ExtMcpToolDecorator implemented with prefix support
- ⏳ Automatic TRACE logging integrated into decorator
- ⏳ Result[T] pattern with instruction field
- ⏳ Base Pydantic model for tool arguments
- ⏳ Explicit use pattern with Literal types
- ⏳ Pydantic validation integration
- ⏳ All tests pass
- ⏳ ADR-008 published
- ⏳ Tool implementation guide available

### Phase 3: Tool Implementations ✅ MOSTLY COMPLETE
- ✅ Each tool uses ExtMcpToolDecorator
- ✅ Each tool returns Result[T] with instruction field
- ✅ Destructive tools use explicit use pattern (if applicable)
- ✅ Tool descriptions include auto-generated schema
- ✅ Tests verify conventions followed
- ✅ Integration tests cover workflows
- ✅ Validation prevents unsafe operations (category/collection tools)
- ✅ Content formatting correct (single vs multiple matches)

### Phase 4: Advanced Features
- ⏳ Template discovery and rendering works
- ⏳ Feature flag integration functional
- ⏳ OpenSpec conditional activation works
- ⏳ Template context hierarchy resolves correctly

---

## Current Status Summary (2025-12-10)

**✅ Completed (6 changes):**
- logging-implementation
- add-category-tools
- add-collection-tools
- add-content-tools
- add-guide-project-tools
- tool-descriptions

**📋 Ready to Start (2 changes):**
- add-feature-flags (no dependencies)
- tool-conventions (no dependencies)

**📋 Blocked but Proposed (6 changes):**
- add-guide-uri-scheme (needs tool-conventions)
- add-guide-utility-tools (needs tool-conventions)
- add-mcp-discovery-tools (needs tool-conventions)
- collections-with-patterns (needs tool-conventions)
- template-support (needs add-feature-flags)
- add-openspec-support (needs add-feature-flags + template-support)
- hook-uri-templates (needs add-guide-uri-scheme + template-support + add-feature-flags)

**Total Progress:** 159/290+ tasks complete (55%)

---

## Notes

- **Breaking Changes**: tool-conventions may require updates to ADR-003 if instruction field not present
- **Testing Strategy**: Integration tests should verify end-to-end flow from tool call → logging → Result return
- **Documentation**: All tool documentation must use undecorated names per ADR-008
- **Maintenance**: Update this file and ROADMAP.md when creating, completing, or archiving changes
