# Refactor Utils Package - Tasks

## Analysis Phase

- [ ] Audit all utils modules for usage patterns
- [ ] Identify dead/orphaned code
- [ ] Map import dependencies
- [ ] Create detailed migration plan for each module group
- [ ] Document import path changes
- [ ] Plan test updates
- [ ] Identify potential merge conflicts

## Implementation Phase

### Content Package
- [ ] Create `src/mcp_guide/content/` directory structure
- [ ] Create `src/mcp_guide/content/formatters/` subdirectory
- [ ] Move content modules to new locations
- [ ] Update imports in moved modules
- [ ] Update imports across codebase for content modules
- [ ] Run tests for content-related functionality

### Feature Flags
- [ ] Move `flag_utils.py` to `feature_flags/utils.py`
- [ ] Update imports across codebase
- [ ] Run tests for feature flag functionality

### Render Package (expand existing)
- [ ] Move template modules into `render/` package
- [ ] Update imports in moved modules
- [ ] Update imports across codebase for template modules
- [ ] Run tests for template-related functionality

### Discovery Package
- [ ] Create `src/mcp_guide/discovery/` directory
- [ ] Move pattern_matching.py, command_discovery.py, file_discovery.py
- [ ] Update imports in moved modules
- [ ] Update imports across codebase for discovery modules
- [ ] Run tests for discovery-related functionality

### Commands Package
- [ ] Create `src/mcp_guide/commands/` directory
- [ ] Move command_formatting.py and command_security.py
- [ ] Update imports in moved modules
- [ ] Update imports across codebase for command modules
- [ ] Run tests for command-related functionality

## Verification Phase

- [ ] Run full test suite
- [ ] Run mypy type checking
- [ ] Run ruff linting
- [ ] Verify no broken imports
- [ ] Check for any missed import updates

## Documentation Phase

- [ ] Update architecture documentation
- [ ] Update developer guide
- [ ] Update any module-specific README files
- [ ] Document new package structure

## Cleanup Phase

- [ ] Remove empty utils/ directory if fully migrated
- [ ] Update .gitignore if needed
- [ ] Remove any deprecated import paths
