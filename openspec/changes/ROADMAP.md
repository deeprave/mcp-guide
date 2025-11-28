# mcp-guide Implementation Roadmap

> **⚠️ MAINTENANCE REQUIRED**: Update this file when:
> - Creating new change proposals
> - Completing/archiving changes
> - Adding new tool groups or phases
> - Changing implementation priorities
>
> **See also:** [IMPLEMENTATION_ORDER.md](./IMPLEMENTATION_ORDER.md) for detailed dependencies

## Overview

This roadmap tracks the phased implementation of mcp-guide, organized by functional areas. Each phase builds on previous phases, with some parallel work possible within Phase 3.

## Phase 1: Foundation (mcp_core)

**Goal:** Establish reusable logging infrastructure for all MCP servers

### logging-implementation
**Status:** ✅ Complete (Ready for archive)
**ADR:** 004-logging-architecture
**JIRA:** GUIDE-2
**Epic:** GUIDE-24
**Completed:** 2025-11-27

**Deliverables:**
- ✅ `src/mcp_core/mcp_log.py` - Core logging module with TRACE level (92% coverage)
- ✅ `src/mcp_core/mcp_log_filter.py` - PII redaction stub (100% coverage)
- ✅ WatchedFileHandler for Unix/Linux file rotation support
- ✅ JSON and text formatters with redaction integration
- ✅ mcp_guide integration (config.py, main.py)
- ✅ Documentation and tests (31 tests passing)

**Success Criteria:**
- ✅ TRACE level functional
- ✅ File logging with JSON works
- ✅ Logger hierarchy prevents duplication
- ✅ >80% test coverage achieved (92%)

---

## Phase 2: Tool Infrastructure

**Goal:** Establish conventions and infrastructure for all MCP tools

### tool-conventions
**Status:** Proposed
**ADR:** 008-tool-definition-conventions
**Requires:** ✅ logging-implementation (Complete)
**Blocks:** All tool implementations (Phase 3)

**Deliverables:**
- ExtMcpToolDecorator with name prefixing and automatic logging
- Result[T] pattern (verify ADR-003 has instruction field)
- Base Pydantic model for tool arguments
- Explicit use pattern with Literal types
- Tool implementation guide and examples
- Documentation and tests

**Success Criteria:**
- Decorator supports prefix configuration
- Automatic TRACE logging on tool calls
- Result[T] with instruction field
- Pydantic validation working
- Example tool demonstrating all patterns

---

## Phase 3: Tool Implementations

**Goal:** Implement all mcp-guide tools following established conventions

**Note:** Phase 3 groups can proceed in parallel after Phase 2 completes. However, within guide-content-tools, category/collection/document operations should be implemented together as they are foundational.

### Phase 3a: Content and Configuration Tools (FOUNDATIONAL - Implement First)
**Status:** Proposed
**Requires:** tool-conventions
**Priority:** HIGH - Core functionality

**Rationale:** Content retrieval and configuration management are the cornerstone of mcp-guide. All other tools depend on this foundation.

**Changes:**

#### add-content-tools (28 tasks)
**Status:** Proposed
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `get_content` - Unified category/collection content access
- `get_category_content` - Category-specific content retrieval
- `get_collection_content` - Collection-specific content retrieval

**Features:**
- Result pattern responses with error instructions
- Pattern-based content filtering (glob syntax)
- Single match → plain markdown
- Multiple matches → MIME multipart format
- Agent-friendly error handling

**Success Criteria:**
- ✅ All three tools implemented
- ✅ Pattern matching works (glob syntax)
- ✅ MIME multipart formatting correct
- ✅ Result pattern with instructions
- ✅ Integration tests cover workflows

#### add-category-tools (44 tasks)
**Status:** Proposed
**Requires:** tool-conventions

**Tools:**
- `category_add` - Create new category
- `category_remove` - Delete category (auto-removes from collections)
- `category_change` - Replace category configuration
- `category_update` - Modify specific fields (add/remove patterns)

**Features:**
- Comprehensive validation (name, dir, description, patterns)
- Traversal prevention and path safety
- Auto-update collections on remove/rename
- Change vs update semantics (replace vs modify)

**Success Criteria:**
- ✅ All CRUD operations working
- ✅ Validation prevents unsafe operations
- ✅ Auto-update collections works
- ✅ Configuration persistence safe

#### add-collection-tools (43 tasks)
**Status:** Proposed
**Requires:** tool-conventions, add-category-tools (for validation)

**Tools:**
- `collection_add` - Create new collection
- `collection_remove` - Delete collection
- `collection_change` - Replace collection configuration
- `collection_update` - Modify specific fields (add/remove categories)

**Features:**
- Category reference validation (referential integrity)
- Change vs update semantics (replace vs modify)
- Comprehensive validation (name, description, categories)

**Success Criteria:**
- ✅ All CRUD operations working
- ✅ Category references validated
- ✅ Configuration persistence safe
- ✅ Integration with category tools

#### add-guide-uri-scheme (17 tasks)
**Status:** Proposed
**Requires:** tool-conventions, add-content-tools

**Features:**
- MCP `resources/list` handler with guide:// URIs
- MCP `resources/read` handler for URI resolution
- URI patterns: help, collection/{id}, category/{name}, category/{name}/{docId}, document/{context}/{docId}
- Delegates to content tools for retrieval

**Success Criteria:**
- ✅ Resources list returns templates
- ✅ URI parsing works correctly
- ✅ Content delegation functional
- ✅ guide://help provides documentation

**Implementation Order:**
1. add-category-tools (category management)
2. add-collection-tools (collection management, depends on categories)
3. add-content-tools (content retrieval, depends on both)
4. add-guide-uri-scheme (resources layer, depends on content tools)

---

### Phase 3b: Project, Utility, and Discovery Tools
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Priority:** MEDIUM - Supporting functionality

**Changes:**

#### add-guide-project-tools (Placeholder)
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `get_current_project` - Returns all data about current project
- `set_current_project` - Sets current project by name, creating if required
- `clone_project` - Copy existing project to current or new project

**Success Criteria:**
- TBD when detailed proposal created

#### add-guide-utility-tools (Placeholder)
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `get_agent_info` - Returns information about agent/client

**Success Criteria:**
- TBD when detailed proposal created

#### add-mcp-discovery-tools (Placeholder)
**Status:** Placeholder
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `list_prompts` - Enumerate available prompts
- `list_resources` - Enumerate available resources
- `list_tools` - Enumerate available tools

**Success Criteria:**
- TBD when detailed proposal created
**Status:** Not Started
**Requires:** tool-conventions
**Priority:** MEDIUM - Project management

**Tools:**
- `get_current_project` - Get active project name
- `switch_project` - Change active project
- `clone_project` - Duplicate project configuration
- `get_project_config` - Retrieve project settings
- `set_project_config` - Update project settings
- `set_project_config_values` - Batch update settings

**Success Criteria:**
- Project switching works correctly
- Configuration persistence
- Clone preserves all settings
- Validation prevents invalid configs

---

### Phase 3c: guide-utilities-tools
**Status:** Not Started
**Requires:** tool-conventions
**Priority:** LOW - Nice to have

**Tools:**
- `get_agent_info` - Retrieve agent metadata and context

**Success Criteria:**
- Agent info captured correctly
- Useful for debugging and logging

---

### Phase 3d: mcp-discovery-tools
**Status:** Not Started
**Requires:** tool-conventions
**Priority:** LOW - Introspection

**Tools:**
- `list_tools` - Enumerate available tools
- `list_prompts` - Enumerate available prompts
- `list_resources` - Enumerate available resources (possibly)

**Success Criteria:**
- Complete tool/prompt/resource enumeration
- Useful metadata included
- Helps agents discover capabilities

---

## Implementation Notes

### Parallel Work Opportunities

After Phase 2 completes:
- Phase 3b, 3c, 3d can proceed in parallel
- Phase 3a should complete first (foundational)
- Within Phase 3a, implement in order: categories → collections → documents → content access

### Testing Strategy

- **Unit tests**: Each tool in isolation
- **Integration tests**: Tool workflows (e.g., create category → add document → retrieve content)
- **Convention tests**: Verify all tools follow ADR-008 patterns

### Documentation Requirements

Each tool group must include:
- API reference with auto-generated schemas
- Usage examples
- Error handling patterns
- Integration with other tools

---

## Status Legend

- **Proposed**: Change proposal created, awaiting approval
- **In Progress**: Implementation underway
- **Complete**: Implemented, tested, documented
- **Archived**: Completed and archived via `openspec archive`
- **Blocked**: Waiting on dependencies
- **Not Started**: Planned but not yet begun

---

## Maintenance Checklist

When creating a new change proposal:
- [ ] Add to appropriate phase in this roadmap
- [ ] Update IMPLEMENTATION_ORDER.md with dependencies
- [ ] Mark status as "Proposed"
- [ ] Add success criteria

When completing a change:
- [ ] Update status to "Complete"
- [ ] Verify dependent changes can now proceed
- [ ] Update IMPLEMENTATION_ORDER.md

When archiving a change:
- [ ] Update status to "Archived"
- [ ] Add archive date
- [ ] Remove from IMPLEMENTATION_ORDER.md active list
