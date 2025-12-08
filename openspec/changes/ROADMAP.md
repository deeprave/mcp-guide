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

### Phase 3a: Content and Configuration Tools (FOUNDATIONAL)
**Status:** ✅ Mostly Complete (3/4 changes complete)
**Requires:** tool-conventions
**Priority:** HIGH - Core functionality

**Rationale:** Content retrieval and configuration management are the cornerstone of mcp-guide. All other tools depend on this foundation.

**Changes:**

#### add-category-tools (44 tasks)
**Status:** ✅ Complete
**Requires:** tool-conventions

**Tools:**
- `category_list` - List all categories
- `category_add` - Create new category
- `category_remove` - Delete category (auto-removes from collections)
- `category_change` - Replace category configuration
- `category_update` - Modify specific fields (add/remove patterns)
- `get_category_content` - Retrieve category content

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
**Status:** ✅ Complete
**Requires:** tool-conventions, add-category-tools (for validation)

**Tools:**
- `collection_list` - List all collections
- `collection_add` - Create new collection
- `collection_remove` - Delete collection
- `collection_change` - Replace collection configuration
- `collection_update` - Modify specific fields (add/remove categories)
- `get_collection_content` - Retrieve collection content

**Features:**
- Category reference validation (referential integrity)
- Change vs update semantics (replace vs modify)
- Comprehensive validation (name, description, categories)

**Success Criteria:**
- ✅ All CRUD operations working
- ✅ Category references validated
- ✅ Configuration persistence safe
- ✅ Integration with category tools

#### add-content-tools (28 tasks)
**Status:** 🔄 In Progress (57% complete - 16/28 tasks)
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `get_content` - Unified category/collection content access
- `get_category_content` - Category-specific content retrieval (✅ Complete)
- `get_collection_content` - Collection-specific content retrieval (✅ Complete)

**Features:**
- Result pattern responses with error instructions
- Pattern-based content filtering (glob syntax)
- Single match → plain markdown
- Multiple matches → MIME multipart format
- Agent-friendly error handling

**Success Criteria:**
- ⏳ All three tools implemented (2/3 complete)
- ✅ Pattern matching works (glob syntax)
- ✅ MIME multipart formatting correct
- ✅ Result pattern with instructions
- ✅ Integration tests cover workflows

#### add-guide-uri-scheme (17 tasks)
**Status:** 📋 Proposed (0% complete)
**Requires:** tool-conventions, add-content-tools

**Features:**
- MCP `resources/list` handler with guide:// URIs
- MCP `resources/read` handler for URI resolution
- URI patterns: help, collection/{id}, category/{name}, category/{name}/{docId}, document/{context}/{docId}
- Delegates to content tools for retrieval

**Success Criteria:**
- ⏳ Resources list returns templates
- ⏳ URI parsing works correctly
- ⏳ Content delegation functional
- ⏳ guide://help provides documentation

**Implementation Order:**
1. ✅ add-category-tools (category management)
2. ✅ add-collection-tools (collection management, depends on categories)
3. 🔄 add-content-tools (content retrieval, depends on both) - IN PROGRESS
4. 📋 add-guide-uri-scheme (resources layer, depends on content tools) - BLOCKED

---

### Phase 3b: Project, Utility, and Discovery Tools
**Status:** ✅ Partially Complete (1/3 changes complete)
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**Priority:** MEDIUM - Supporting functionality

**Changes:**

#### add-guide-project-tools
**Status:** ✅ Complete (2025-12-08)
**Requires:** tool-conventions, add-category-tools, add-collection-tools
**JIRA:** GUIDE-110, GUIDE-111, GUIDE-112, GUIDE-113, GUIDE-114, GUIDE-115

**Tools:**
- `get_current_project` - Returns all data about current project
- `set_current_project` - Sets current project by name, creating if required
- `clone_project` - Copy existing project to current or new project
- `list_projects` - List all available projects
- `list_project` - Get specific project details

**Features:**
- Verbose/non-verbose output modes
- Project creation on demand
- Clone with merge/replace modes and safeguards
- Conflict detection and warnings
- Automatic cache reload

**Success Criteria:**
- ✅ All 5 tools implemented and tested
- ✅ 21 integration tests covering all workflows
- ✅ MCP tool documentation complete (descriptions + schemas)
- ✅ 641 tests passing, 90% coverage
- ✅ Pydantic Field descriptions exposed in MCP schemas

**Key Achievement:**
Enhanced `ExtMcpToolDecorator` to preserve Pydantic Field descriptions in MCP schemas by passing models as single `args` parameter. This improvement benefits all tools in mcp-guide.

#### add-guide-utility-tools
**Status:** 📋 Proposed (0% complete)
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `get_agent_info` - Returns information about agent/client

**Success Criteria:**
- ⏳ Agent info captured correctly
- ⏳ Useful for debugging and logging

#### add-mcp-discovery-tools
**Status:** 📋 Proposed (0% complete)
**Requires:** tool-conventions, add-category-tools, add-collection-tools

**Tools:**
- `list_prompts` - Enumerate available prompts
- `list_resources` - Enumerate available resources
- `list_tools` - Enumerate available tools

**Success Criteria:**
- ⏳ Complete tool/prompt/resource enumeration
- ⏳ Useful metadata included
- ⏳ Helps agents discover capabilities

---

### Phase 3c: Feature Enhancements
**Status:** 📋 Proposed
**Priority:** LOW - Nice to have

**Changes:**

#### collections-with-patterns
**Status:** 📋 Proposed (0% complete)
**Requires:** add-collection-tools

**Features:**
- Allow collections to override category patterns
- Per-collection pattern customization
- Backward compatibility with existing collections

**Success Criteria:**
- ⏳ Collections can specify custom patterns
- ⏳ Pattern override works correctly
- ⏳ Existing collections unaffected

---

## Implementation Notes

### Current Progress (2025-12-08)

**Completed Changes (3):**
- ✅ add-category-tools (44 tasks)
- ✅ add-collection-tools (43 tasks)
- ✅ add-guide-project-tools (34 tasks)

**In Progress (1):**
- 🔄 add-content-tools (16/28 tasks, 57% complete)

**Proposed/Blocked (4):**
- 📋 add-guide-uri-scheme (blocked by add-content-tools)
- 📋 add-guide-utility-tools
- 📋 add-mcp-discovery-tools
- 📋 collections-with-patterns

**Total Progress:** 40/96 tasks complete (42%)

### Parallel Work Opportunities

After Phase 2 completes:
- Phase 3a changes can proceed in order: categories → collections → content → URI scheme
- Phase 3b changes can proceed in parallel with Phase 3a (project tools complete)
- Phase 3c can proceed after Phase 3a completes

### Key Achievements

1. **MCP Schema Enhancement (2025-12-08):**
   - Modified `ExtMcpToolDecorator` to preserve Pydantic Field descriptions
   - All tools now expose complete argument documentation to MCP clients
   - Nested `{"args": {...}}` structure follows Pydantic best practices

2. **Tool Infrastructure:**
   - Result pattern with error instructions
   - Comprehensive validation and error handling
   - Integration test coverage for all workflows

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

- **✅ Complete**: Implemented, tested, documented, ready for archive
- **🔄 In Progress**: Implementation underway with partial completion
- **📋 Proposed**: Change proposal created, awaiting implementation
- **⏳ Pending**: Waiting on dependencies or blocked
- **Archived**: Completed and archived via `openspec archive`

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
