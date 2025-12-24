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
**Status:** ✅ Complete
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
- ✅ Feature flags stored in configuration models
- ✅ MCP tools provide complete flag management
- ✅ Resolution hierarchy works correctly
- ✅ Immediate persistence on flag changes
- ✅ Validation prevents invalid flag names/values

#### 3. tool-conventions
**Status:** ✅ Complete
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
**Status:** ✅ Complete
**Requires:** ✅ tool-conventions (Complete), ✅ add-content-tools (Complete)
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
**Status:** ✅ Complete
**Requires:** ✅ tool-conventions (Complete)
**Priority:** LOW - Utilities

**Tools:**
- get_agent_info - Returns information about agent/client

**Validation:**
- ✅ Agent info captured correctly
- ✅ Useful for debugging and logging

#### 4g. add-mcp-discovery-tools
**Status:** ✅ Complete
**Requires:** ✅ tool-conventions (Complete)
**Priority:** LOW - Introspection

**Tools:**
- list_prompts - Enumerate available prompts
- list_resources - Enumerate available resources
- list_tools - Enumerate available tools

**Validation:**
- ✅ Complete tool/prompt/resource enumeration
- ✅ Useful metadata included
- ✅ Helps agents discover capabilities

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
**Status:** ✅ Complete
**Requires:** ✅ add-collection-tools (Complete)
**Priority:** LOW - Enhancement

**Features:**
- Allow collections to override category patterns
- Per-collection pattern customization
- Backward compatibility with existing collections

**Validation:**
- ✅ Collections can specify custom patterns
- ✅ Pattern override works correctly
- ✅ Existing collections unaffected

---

### Phase 4: Advanced Features

#### 5a. agent-server-filesystem-interaction
**Status:** 📋 Proposed (0% complete)
**Requires:** ✅ logging-implementation (Complete)
**Blocks:** add-openspec-support
**Priority:** HIGH - Filesystem interaction infrastructure

**Deliverables:**
- Sampling-based file operations (directory listing, file reading)
- Path validation and security fencing
- Server-side file caching with LRU eviction
- MCP tools: guide_cache_file, guide_list_directory, guide_read_file
- OpenSpec filesystem integration

**Validation:**
- ⏳ Directory listing via sampling requests works
- ⏳ File reading via sampling requests works
- ⏳ Path security fencing prevents unauthorized access
- ⏳ File cache performs efficiently
- ⏳ OpenSpec tools use filesystem interaction

#### 5b. template-support
**Status:** ✅ Complete
**Requires:** ✅ add-feature-flags (Complete)
**Blocks:** add-openspec-support
**Priority:** HIGH - Template rendering system

**Features:**
- Mustache/Chevron template rendering
- TemplateContext with ChainMap hierarchy
- Template discovery and rendering pipeline
- Integration with feature flags for conditional rendering

**Validation:**
- ✅ Template discovery works
- ✅ Context hierarchy resolves correctly
- ✅ Chevron rendering functional
- ✅ Feature flag integration complete

#### 5c. add-openspec-support
**Status:** 📋 Proposed (0% complete)
**Requires:** add-feature-flags, template-support, agent-server-filesystem-interaction
**Priority:** MEDIUM - OpenSpec workflow integration

**Features:**
- Conditional OpenSpec detection via feature flags
- MCP tools for OpenSpec workflows
- MCP resources for OpenSpec project state
- Template context integration
- Dynamic file discovery and validation

**Validation:**
- ⏳ Feature flag conditional activation
- ⏳ OpenSpec workflow tools functional
- ⏳ Template integration complete
- ⏳ MCP resources queryable
- ⏳ Filesystem interaction enables dynamic change discovery

#### 5d. hook-uri-templates
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
    ✅ add-feature-flags - COMPLETE
    ✅ tool-conventions (ADR-008) - COMPLETE
        ↓
Phase 3: Tool Implementations
    ✅ add-category-tools (4a) - COMPLETE
        ↓
    ✅ add-collection-tools (4b) - COMPLETE
        ↓
    ✅ add-content-tools (4c) - COMPLETE
        ↓
    ✅ add-guide-uri-scheme (4d) - COMPLETE

    Parallel (depend on tool-conventions only):
    ✅ add-guide-project-tools (4e) - COMPLETE
    ✅ add-guide-utility-tools (4f) - COMPLETE
    ✅ add-mcp-discovery-tools (4g) - COMPLETE
    ✅ tool-descriptions (4h) - COMPLETE
    ✅ collections-with-patterns (4i) - COMPLETE

Phase 4: Advanced Features
    📋 agent-server-filesystem-interaction (5a) ← depends on logging-implementation (Complete) - READY TO START
    ✅ template-support (5b) - COMPLETE
        ↓
    📋 add-openspec-support (5c) ← depends on template-support + agent-server-filesystem-interaction
    📋 hook-uri-templates (5d) ← depends on add-guide-uri-scheme + template-support
```

**Critical Path:**
1. ✅ logging-implementation (Complete)
2. ✅ add-feature-flags (Complete)
3. ✅ tool-conventions (Complete)
4. ✅ template-support (Complete)
5. 📋 agent-server-filesystem-interaction (enables OpenSpec filesystem access) - READY TO START
6. 📋 add-openspec-support (after agent-server-filesystem-interaction)
7. 📋 hook-uri-templates (optional enhancement)

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

### agent-server-filesystem-interaction → add-openspec-support
**Reason:** OpenSpec integration requires dynamic file discovery and validation
**Impact:** Cannot implement interactive OpenSpec workflows without filesystem access
**Validation:** Sampling-based file operations and caching must work before OpenSpec integration

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

### ✅ All Phases Complete Except Phase 4 Final Items

**Phase 1: Foundation** ✅ COMPLETE
- logging-implementation

**Phase 2: Configuration and Infrastructure** ✅ COMPLETE
- add-feature-flags
- tool-conventions

**Phase 3: Tool Implementations** ✅ COMPLETE
- All content and configuration tools (4a-4c)
- add-guide-uri-scheme (4d)
- All utility and discovery tools (4e-4g)
- tool-descriptions (4h)
- collections-with-patterns (4i)

**Phase 4: Advanced Features** - IN PROGRESS
- ✅ template-support (5b) - COMPLETE
- 📋 agent-server-filesystem-interaction (5a) - READY TO START
- 📋 add-openspec-support (5c) - Waiting for agent-server-filesystem-interaction
- 📋 hook-uri-templates (5d) - Optional enhancement

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
- ⏳ Sampling-based filesystem operations work correctly
- ⏳ Path security fencing prevents unauthorized access
- ⏳ File cache performs efficiently with LRU eviction
- ⏳ Template discovery and rendering works
- ⏳ Feature flag integration functional
- ⏳ OpenSpec conditional activation works
- ⏳ OpenSpec dynamic file discovery functional
- ⏳ Template context hierarchy resolves correctly

---

## Current Status Summary (2025-12-24)

**✅ Completed (13 changes):**
- logging-implementation
- add-feature-flags
- tool-conventions
- add-category-tools
- add-collection-tools
- add-content-tools
- add-guide-uri-scheme
- add-guide-project-tools
- add-guide-utility-tools
- add-mcp-discovery-tools
- tool-descriptions
- collections-with-patterns
- template-support

**📋 Ready to Start (1 change):**
- agent-server-filesystem-interaction (depends on logging-implementation, which is complete)

**📋 Blocked but Proposed (2 changes):**
- add-openspec-support (needs agent-server-filesystem-interaction + template-support - template-support is complete)
- hook-uri-templates (optional enhancement - all dependencies complete)

**Total Progress:** 13/16 changes complete (81%)

---

## Notes

- **Breaking Changes**: tool-conventions may require updates to ADR-003 if instruction field not present
- **Testing Strategy**: Integration tests should verify end-to-end flow from tool call → logging → Result return
- **Documentation**: All tool documentation must use undecorated names per ADR-008
- **Maintenance**: Update this file and ROADMAP.md when creating, completing, or archiving changes
