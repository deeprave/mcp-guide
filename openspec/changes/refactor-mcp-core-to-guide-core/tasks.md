## 1. Analysis and Planning
- [x] 1.1 Audit all current imports of `mcp_core` across the codebase
- [x] 1.2 Identify external dependencies and API surface
- [x] 1.3 Plan migration strategy for import paths
- [x] 1.4 Review package structure and dependencies

## 2. Directory Structure Changes
- [x] 2.1 Create `src/mcp_guide/core/` directory
- [x] 2.2 Move all files from `src/mcp_core/` to `src/mcp_guide/core/`
- [x] 2.3 Update `__init__.py` files for proper module structure
- [x] 2.4 Remove old `src/mcp_core/` directory

## 3. Import Path Updates
- [x] 3.1 Update imports in `src/mcp_guide/` files
- [x] 3.2 Update imports in test files
- [x] 3.3 Update any configuration or setup files
- [x] 3.4 Verify no remaining `mcp_core` imports

## 4. Package Configuration
- [x] 4.1 Update `pyproject.toml` package configuration
- [x] 4.2 Update package discovery settings
- [x] 4.3 Update any entry points or scripts
- [x] 4.4 Verify package structure is correct

## 5. Testing and Validation
- [x] 5.1 Run full test suite to verify functionality
- [x] 5.2 Test package installation and imports
- [x] 5.3 Verify no import errors or missing modules
- [x] 5.4 Test CLI functionality end-to-end

## 6. Documentation Updates
- [x] 6.1 Update any documentation referencing `mcp_core`
- [x] 6.2 Update README or installation instructions if needed
- [x] 6.3 Update any code examples or snippets
