# Disambiguate Feature Flag Tools

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

The current feature flag tools (`set_flag`, `get_flag`, `list_flags`) are ambiguous about whether they operate on project flags or global flags. While they currently work with project flags by default, this creates confusion for users who need to manage global flags separately.

The existing implementation has:
- Project flags accessible via `session.project_flags()`
- Global flags accessible via `session.feature_flags()`
- Tools that only work with project flags, leaving global flags unmanageable via MCP

This ambiguity makes it unclear:
- Which scope flags are being set/retrieved
- How to manage global flags that apply across all projects
- The relationship between project and global flag resolution

## What Changes

**Rename existing tools to be explicit about project scope:**
- `set_flag` → `set_project_flag`
- `get_flag` → `get_project_flag`
- `list_flags` → `list_project_flags`

**Add new tools for global flag management:**
- `set_feature_flag` - Set global flags only
- `get_feature_flag` - Get global flags only
- `list_feature_flags` - List global flags only

**Maintain existing behavior:**
- Project flag tools preserve current resolution hierarchy (project overrides global)
- Global flag tools operate exclusively on `session.feature_flags()`
- No breaking changes to flag storage or resolution logic

## Technical Approach

1. Rename existing functions and their argument classes
2. Create new argument classes for global flag operations
3. Implement global flag functions using `session.feature_flags()`
4. Update tests to use new function names
5. Ensure 100% backward compatibility in flag behavior

## Success Criteria

- All existing functionality preserved with new names
- Global flags manageable via MCP tools
- Clear separation between project and global flag operations
- 100% test pass rate with no regressions
