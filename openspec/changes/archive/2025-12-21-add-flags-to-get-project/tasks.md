# Implementation Tasks

## Phase 1: Analysis
- [x] Review current `guide_get_project` implementation in `src/mcp_guide/tools/tool_project.py`
- [x] Identify where project flags should be added to the response
- [x] Check if Project model needs modification or if response can be enhanced directly

## Phase 2: Implementation
- [x] Modify `internal_get_project` function to include resolved project flags
- [x] Add flags to the response structure when `verbose=true`
- [x] Ensure flags are fully resolved using session's project flags API
- [x] Update any type hints or response models if needed

## Phase 3: Testing
- [x] Test `guide_get_project(verbose=true)` includes flags
- [x] Test `guide_get_project(verbose=false)` behavior unchanged
- [x] Verify flags are fully resolved (include global + project flags)
- [x] Test with projects that have no flags set
- [x] Test with projects that have only global flags
- [x] Test with projects that have both global and project-specific flags

## Phase 4: Check
- [x] Run existing tests to ensure no regressions
- [x] Verify backward compatibility
- [x] Check that flag resolution works correctly
- [x] Manual testing with actual MCP client

## Phase 5: Additional Consistency Fixes (Discovered during implementation)
- [x] Fix `list_all_projects` to include session parameter for flag resolution
- [x] Fix `get_project_info` to include session parameter for flag resolution
- [x] Fix `set_project` to consistently include flags (empty if no session)
- [x] Improve `_resolve_all_flags` error handling with debug logging
- [x] Replace type ignore comments with explicit Union type annotations
- [x] Verify all project tools have consistent flag behavior
- [x] Run comprehensive tests for flag consistency across all tools
