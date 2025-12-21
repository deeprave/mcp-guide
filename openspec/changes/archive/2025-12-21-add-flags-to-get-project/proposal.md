# Add Flags to get_project Tool

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

The `get_project` tool currently returns incomplete project configuration - it only includes categories and collections but omits project flags. This creates an inconsistent API where users must make separate calls to `list_project_flags` to get the complete project state.

Project flags are a core part of project configuration and should be included in the project data structure returned by `get_project`, especially when `verbose=true` is specified.

## What Changes

- Modify `guide_get_project` tool to include resolved project flags in the response
- Flags should be fully resolved (project flags merged with global feature flags)
- Update the Project model or response structure to include a `flags` field
- Ensure backward compatibility for existing consumers

## Technical Approach

The `get_project` tool should call the session's project flags API to get the fully resolved flags and include them in the response alongside categories and collections.

## Success Criteria

- `guide_get_project(verbose=true)` returns project flags
- Flags are fully resolved (include both project-specific and global flags)
- Existing functionality remains unchanged
