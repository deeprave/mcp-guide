# Implementation Tasks

## Phase 1: Analysis
- [ ] Review current `guide_get_project` implementation in `src/mcp_guide/tools/tool_project.py`
- [ ] Identify where project flags should be added to the response
- [ ] Check if Project model needs modification or if response can be enhanced directly

## Phase 2: Implementation
- [ ] Modify `internal_get_project` function to include resolved project flags
- [ ] Add flags to the response structure when `verbose=true`
- [ ] Ensure flags are fully resolved using session's project flags API
- [ ] Update any type hints or response models if needed

## Phase 3: Testing
- [ ] Test `guide_get_project(verbose=true)` includes flags
- [ ] Test `guide_get_project(verbose=false)` behavior unchanged
- [ ] Verify flags are fully resolved (include global + project flags)
- [ ] Test with projects that have no flags set
- [ ] Test with projects that have only global flags
- [ ] Test with projects that have both global and project-specific flags

## Phase 4: Check
- [ ] Run existing tests to ensure no regressions
- [ ] Verify backward compatibility
- [ ] Check that flag resolution works correctly
- [ ] Manual testing with actual MCP client
