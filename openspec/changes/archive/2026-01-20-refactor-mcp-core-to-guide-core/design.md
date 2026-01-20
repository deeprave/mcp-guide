## Context

The mcp-guide project currently has a split module structure with `mcp_core` containing reusable components and `mcp_guide` containing application-specific code. This creates packaging complexity and user confusion, as installing one package results in two separate module trees.

## Goals / Non-Goals

**Goals:**
- Consolidate into single `mcp_guide` package structure
- Maintain logical separation of core vs application code
- Preserve all existing APIs and functionality
- Simplify package distribution and installation

**Non-Goals:**
- Changing any core functionality or APIs
- Restructuring internal module organization beyond the move
- Breaking backward compatibility within the same major version

## Decisions

**Decision: Move to `mcp_guide.core` namespace**
- **Rationale**: Maintains clear separation while consolidating package structure
- **Alternatives considered**:
  - Merge directly into `mcp_guide` (rejected: loses logical separation)
  - Keep separate packages (rejected: packaging complexity)
  - Create `mcp_guide.lib` (rejected: less clear naming)

**Decision: Preserve exact API surface**
- **Rationale**: Minimizes migration effort and maintains compatibility
- **Implementation**: Direct file moves with import path updates only

## Migration Plan

1. **Preparation**: Audit all imports and create comprehensive test coverage
2. **Move**: Relocate files from `src/mcp_core/` to `src/mcp_guide/core/`
3. **Update**: Mass find/replace of import statements
4. **Validate**: Full test suite execution and package installation testing
5. **Rollback**: If issues arise, reverse the file moves and import changes

## Risks / Trade-offs

**Risk: Import path changes break external usage**
- **Mitigation**: This is internal refactoring; no external API exposure expected

**Risk: Circular import issues with new structure**
- **Mitigation**: Core modules should not import from application modules; verify during testing

**Risk: Package discovery issues**
- **Mitigation**: Update `pyproject.toml` package configuration and test installation
