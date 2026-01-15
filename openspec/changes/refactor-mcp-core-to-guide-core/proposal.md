# Change: Refactor mcp_core module into mcp_guide/core

## Why

The current project structure has `mcp_core` as a separate top-level module alongside `mcp_guide`, which creates unnecessary complexity for distribution and installation. Users must install a single package but get two separate modules. Consolidating `mcp_core` into `mcp_guide/core` provides:

- Single cohesive package structure
- Simplified installation (one package, one module tree)
- Maintained logical separation of reusable core components
- Cleaner import paths within the project

## What Changes

- **BREAKING**: Move `src/mcp_core/` → `src/mcp_guide/core/`
- Update all import statements from `mcp_core.*` → `mcp_guide.core.*`
- Update package configuration in `pyproject.toml`
- Maintain all existing APIs and functionality
- Update documentation references

## Impact

- Affected specs: None (no functional changes)
- Affected code: All files importing from `mcp_core` (approximately 50+ files)
- Breaking change: Import paths change but APIs remain identical
- Migration: Simple find/replace of import statements
