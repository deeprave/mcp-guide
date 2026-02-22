# Change: Reorganize Project Management Commands

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

Consolidate project management commands under `project/*` namespace:

1. **`project/category [action] [name] [args]`** - Category management
   - Calls unified `category` tool from `refactor-combine-tools`
   - Actions: list, add, remove, change, update, files
   - Example: `project/category list`, `project/category add docs`

2. **`project/collection [action] [name] [args]`** - Collection management
   - Calls unified `collection` tool from `refactor-combine-tools`
   - Actions: list, add, remove, change, update
   - Example: `project/collection list`, `project/collection add getting-started`

3. **`project/info`** - Project information
   - Moved from `info/project`
   - Alias: `info/project` → `project/info` for compatibility

4. **`project/perm [action] [file] [read|write] [args]`** - Permission management
   - Moved from `perm/*`
   - Actions: add, del (for read/write permissions)
   - Example: `project/perm add myfile.txt write`

**Removed:**
- `create/category` - Use `project/category add` instead
- `create/collection` - Use `project/collection add` instead
- `perm/*` - Use `project/perm` instead

**Unchanged:**
- `workflow/*` commands - Stay as-is
- `openspec/*` commands - Stay as-is
- `info/agent`, `info/flags`, `info/system` - Stay as-is
- `status` command - Stays as-is

## Impact

- **Affected specs**: `help-template-system`
- **Affected code**: `src/mcp_guide/templates/_commands/` - create, info, perm directories
- **Dependencies**: **BLOCKS ON** `refactor-combine-tools` completion (needs unified tools)
- **Benefits**:
  - All project management in one namespace
  - Consistent action-first syntax across commands
  - Clearer command organization
  - Removes confusing "create" namespace
- **Compatibility**: `info/project` aliased to `project/info`
