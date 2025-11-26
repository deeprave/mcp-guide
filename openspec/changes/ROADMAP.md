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
**Status:** Proposed
**ADR:** 004-logging-architecture
**Blocks:** All subsequent phases (tool-conventions requires TRACE logging)

**Deliverables:**
- `src/mcp_core/mcp_log.py` - Core logging module with TRACE level
- `src/mcp_core/mcp_log_filter.py` - PII redaction stub
- WatchedFileHandler for Unix/Linux file rotation support
- JSON and text formatters with redaction integration
- mcp_guide integration (config.py, main.py)
- Documentation and tests

**Success Criteria:**
- TRACE level functional
- File logging with JSON works
- Logger hierarchy prevents duplication
- >80% test coverage

---

## Phase 2: Tool Infrastructure

**Goal:** Establish conventions and infrastructure for all MCP tools

### tool-conventions
**Status:** Proposed
**ADR:** 005-tool-definition-conventions
**Requires:** logging-implementation
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

### Phase 3a: guide-content-tools (FOUNDATIONAL - Implement First)
**Status:** Not Started
**Requires:** tool-conventions
**Priority:** HIGH - Core functionality

**Rationale:** Category, collection, and document operations are the cornerstone of how mcp-guide serves documents. All other tools depend on this foundation.

**Tool Groups:**

#### Category Operations
- `get_category` - Retrieve category configuration
- `add_category` - Create new category
- `update_category` - Modify category settings
- `remove_category` - Delete category
- `list_categories` - List all categories

#### Collection Operations
- `get_collection` - Retrieve collection configuration
- `add_collection` - Create new collection
- `update_collection` - Modify collection settings
- `remove_collection` - Delete collection
- `list_collections` - List all collections

#### Document Operations
- `create_mcp_document` - Upload new document (explicit use)
- `get_mcp_document` - Retrieve document content
- `update_mcp_document` - Modify document (explicit use)
- `delete_mcp_document` - Remove document (explicit use)
- `list_mcp_documents` - List documents in category

#### Content Access
- `get_category_content` - Get content from category
- `get_file_content` - Get raw file content
- `search_content` - Search across categories

**Implementation Strategy:**
1. Implement category operations first (foundation)
2. Implement collection operations (depends on categories)
3. Implement document operations (depends on categories)
4. Implement content access (uses all above)

**Success Criteria:**
- All CRUD operations working
- Explicit use pattern on destructive operations
- Content retrieval efficient
- Search functional across all content
- Integration tests cover workflows

---

### Phase 3b: guide-project-tools
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
- **Convention tests**: Verify all tools follow ADR-005 patterns

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
