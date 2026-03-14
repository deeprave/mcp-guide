# Change: Reorganize Project Management Commands

**JIRA Ticket:** GUIDE-179

## Why

The current command structure has project-related commands scattered across multiple top-level namespaces:
- `create/category` and `create/collection` - Non-intuitive "create" namespace
- `info/project` - Project info buried in generic "info" namespace
- `perm/*` - Permission commands at top level

This creates:
- **Poor discoverability**: Users must know multiple namespaces to manage projects
- **Inconsistent organization**: Related commands are separated
- **Confusing "create" namespace**: Only has 2 commands, unclear purpose

## What Changes

Consolidate project management commands under `project/*` namespace and reorganize flag commands:

### Project Commands

1. **`project/category [action] [name] [args]`** - Category management
   - Template dispatcher calls existing tools: `category_list`, `category_add`, etc.
   - Actions: list, add, remove, change, update, files
   - Example: `project/category list`, `project/category add docs`

2. **`project/collection [action] [name] [args]`** - Collection management
   - Template dispatcher calls existing tools: `collection_list`, `collection_add`, etc.
   - Actions: list, add, remove, change, update
   - Example: `project/collection list`, `project/collection add getting-started`

3. **`project/info`** - Project information
   - Moved from `info/project`
   - Alias: `info/project` → `project/info` for compatibility

4. **`project/perm [action] [type] [path]`** - Permission management
   - View current permissions: `project/perm`
   - Add/remove paths: `project/perm/write/add`, `project/perm/read/add`, etc.
   - **NEW TOOLS REQUIRED**: `add_permission_path`, `remove_permission_path`
   - Actions use MCP tools (not direct config editing)
   - Example: `project/perm/write/add docs/`, `project/perm/read/remove /external/path`

### Flag Commands

5. **`flags/project [action] [name] [args]`** - Project flag management
   - Template dispatcher calls existing tools: `list_project_flags`, `set_project_flag`, `get_project_flag`
   - Actions: list, get, set, remove
   - Example: `flags/project list`, `flags/project set workflow true`

6. **`flags/feature [action] [name] [args]`** - Feature flag management
   - Template dispatcher calls existing tools: `list_feature_flags`, `set_feature_flag`, `get_feature_flag`
   - Actions: list, get, set, remove
   - Example: `flags/feature list`, `flags/feature set openspec true`

7. **`flags` (alias for `flags/project list` + `flags/feature list`)**
   - Shows all flags with descriptions
   - Excludes `guide-development` flag (internal use only)
   - Lists supported flags from `feature_flags/constants.py`

**Removed:**
- `create/category` - Use `project/category add` instead
- `create/collection` - Use `project/collection add` instead
- `perm/*` - Use `project/perm` instead
- `info/flags` - Use `flags` or `flags/project list` / `flags/feature list` instead

**Unchanged:**
- `workflow/*` commands - Stay as-is
- `openspec/*` commands - Stay as-is
- `info/agent`, `info/system` - Stay as-is
- `status` command - Stays as-is

## Impact

- **Affected specs**: `help-template-system`, `config-management`, `project-tools` (NEW)
- **Affected code**:
  - `src/mcp_guide/templates/_commands/` - create, info, perm, flags directories
  - `src/mcp_guide/tools/tool_project.py` - NEW permission management tools
- **New MCP Tools Required**:
  - `add_permission_path(permission_type: "read"|"write", path: str)` - Add path to permissions
  - `remove_permission_path(permission_type: "read"|"write", path: str)` - Remove path from permissions
- **Benefits**:
  - All project management in one namespace
  - Flag management separated by scope (project vs feature)
  - Consistent action-first syntax across commands
  - Clearer command organization
  - Removes confusing "create" namespace
  - Better flag discoverability with descriptions
  - **Proper MCP architecture**: Permission changes via tools, not config editing
- **Compatibility**: `info/project` aliased to `project/info`
