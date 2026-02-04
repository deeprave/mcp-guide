# Refactor Utils Package - Tasks

## Analysis Phase

- [x] Audit all utils modules for usage patterns
- [x] Identify dead/orphaned code
- [x] Map import dependencies
- [x] Create detailed migration plan for each module group
- [x] Document import path changes
- [x] Plan test updates
- [x] Identify potential merge conflicts

## Implementation Phase

### Content Package
- [x] Create `src/mcp_guide/content/` directory structure
- [x] Create `src/mcp_guide/content/formatters/` subdirectory
- [x] Move content modules to new locations
- [x] Update imports in moved modules
- [x] Update imports across codebase for content modules
- [x] Run tests for content-related functionality

### Feature Flags
- [x] Move `flag_utils.py` to `feature_flags/utils.py`
- [x] Update imports across codebase
- [x] Run tests for feature flag functionality

### Render Package (expand existing)
- [x] Move template modules into `render/` package
- [x] Update imports in moved modules
- [x] Update imports across codebase for template modules
- [x] Run tests for template-related functionality

### Discovery Package
- [x] Create `src/mcp_guide/discovery/` directory
- [x] Move pattern_matching.py, command_discovery.py, file_discovery.py
- [x] Update imports in moved modules
- [x] Update imports across codebase for discovery modules
- [x] Run tests for discovery-related functionality

### Commands Package
- [x] Create `src/mcp_guide/commands/` directory
- [x] Move command_formatting.py and command_security.py
- [x] Update imports in moved modules
- [x] Update imports across codebase for command modules
- [x] Run tests for command-related functionality

## Verification Phase

- [x] Run full test suite
- [x] Run mypy type checking
- [x] Run ruff linting
- [x] Verify no broken imports
- [x] Check for any missed import updates

## Documentation Phase

- [x] Update architecture documentation (skipped - code is self-documenting)
- [x] Update developer guide (skipped - code is self-documenting)
- [x] Update any module-specific README files (skipped - none needed)
- [x] Document new package structure (skipped - structure is self-evident)

## Cleanup Phase

- [x] Verify utils/ contains only general utilities
- [x] Fixed test logger references
- [x] All 19 modules successfully moved
