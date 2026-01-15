## 1. Analysis and Planning
- [ ] 1.1 Audit all current imports of `mcp_core` across the codebase
- [ ] 1.2 Identify external dependencies and API surface
- [ ] 1.3 Plan migration strategy for import paths
- [ ] 1.4 Review package structure and dependencies

## 2. Directory Structure Changes
- [ ] 2.1 Create `src/mcp_guide/core/` directory
- [ ] 2.2 Move all files from `src/mcp_core/` to `src/mcp_guide/core/`
- [ ] 2.3 Update `__init__.py` files for proper module structure
- [ ] 2.4 Remove old `src/mcp_core/` directory

## 3. Import Path Updates
- [ ] 3.1 Update imports in `src/mcp_guide/` files
- [ ] 3.2 Update imports in test files
- [ ] 3.3 Update any configuration or setup files
- [ ] 3.4 Verify no remaining `mcp_core` imports

## 4. Package Configuration
- [ ] 4.1 Update `pyproject.toml` package configuration
- [ ] 4.2 Update package discovery settings
- [ ] 4.3 Update any entry points or scripts
- [ ] 4.4 Verify package structure is correct

## 5. Testing and Validation
- [ ] 5.1 Run full test suite to verify functionality
- [ ] 5.2 Test package installation and imports
- [ ] 5.3 Verify no import errors or missing modules
- [ ] 5.4 Test CLI functionality end-to-end

## 6. Documentation Updates
- [ ] 6.1 Update any documentation referencing `mcp_core`
- [ ] 6.2 Update README or installation instructions if needed
- [ ] 6.3 Update any code examples or snippets
