# Change: Consolidate Management Tools into Action-Based Tools

## Why

The current tool set has 35 tools, with significant duplication in CRUD operations across categories, collections, projects, flags, and profiles. Each entity type has separate tools for list, add, remove, change, and update operations, creating:

- **Tool proliferation**: 7 category tools, 5 collection tools, 6 flag tools, etc.
- **Discovery overhead**: Agents must discover and understand many similar tools
- **Maintenance burden**: Changes to patterns require updates across multiple tools
- **Inconsistent patterns**: Slight variations in how similar operations work

## What Changes

Consolidate management tools into 5 action-based tools with consistent patterns:

1. **`category`** - Single tool with actions: `list`, `add`, `remove`, `change`, `update`, `files`
2. **`collection`** - Single tool with actions: `list`, `add`, `remove`, `change`, `update`
3. **`flag`** - Single tool with actions: `list`, `get`, `set` (with `type` parameter for project vs global)
4. **`profile`** - Single tool with actions: `list`, `show`, `use`
5. **`project`** - Single tool with actions: `list`, `get`, `set`, `clone`

**Unchanged:**
- `get_content` - Primary content access tool (not a management operation)
- `category_content` - Specialized content retrieval (not management)
- `list_tools`, `list_prompts`, `list_resources` - MCP introspection
- `send_*` tools - Filesystem communication protocol
- `client_info` - MCP client information

**Implementation approach:**
- Use Pydantic discriminated unions for action-specific arguments
- FastMCP and Pydantic handle validation automatically
- Each action maps to existing internal functions (no logic changes)
- Phased rollout: category → collection → flag → profile → project

## Impact

- **Affected specs**: `category-tools`, `collection-tools`, `guide-project-tools`, `config-management`
- **Affected code**: `src/mcp_guide/tools/` - category, collection, project, flag, profile modules
- **Tool count**: Reduces from 35 to 23 tools (12 fewer tools)
- **Benefits**:
  - Simpler tool discovery for agents
  - Consistent action-based pattern across all management operations
  - Easier to add new actions without new tools
  - Reduced maintenance burden
- **No breaking changes**: Agents discover tools at initialization, no compatibility needed
