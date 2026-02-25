# Change: Fix Critical Missing File Comparison in Install Command

## Why
**CRITICAL BUG**: The `install` command does not implement the file comparison logic specified in the installation spec. It blindly copies all files every time, even when they're unchanged.

**Spec Requirements (NOT IMPLEMENTED):**
- "Async File Comparison" - SHALL compare files using SHA256 to determine if updates needed
- "File identical to new version" - SHALL skip file if current matches new version

**Current State:**
- `install_file()` - NO comparison, always copies (VIOLATES SPEC)
- `smart_update()` - Has comparison logic ✓ (used by update command)
- Tests - NO tests for install_file() comparison behavior
- E2E tests - NO tests verifying unchanged files are skipped

**Additional Issue:**
Both install and update commands report inaccurate statistics (total file count instead of actual operations).

## What Changes
1. **Implement missing spec requirement**: Add file comparison to `install_file()` to skip unchanged files
2. **Fix statistics**: Track and report actual operations (installed/updated/unchanged)
3. **Add missing tests**: Comprehensive unit and E2E tests for file comparison behavior
4. **Add quiet flag**: Support `--quiet`/`-q` to suppress non-error output

## Impact
- Affected specs: `installation` (implementing missing requirements)
- Affected code:
  - `src/mcp_guide/installer/core.py` - `install_file()`, `install_templates()`, `update_templates()`
  - `src/mcp_guide/scripts/mcp_guide_install.py` - output formatting, quiet flag
  - `tests/unit/installer/test_core.py` - Add missing install_file() tests
  - `tests/unit/scripts/test_mcp_guide_install.py` - Add E2E comparison tests
- Breaking: None (fixes bug, improves performance)
- Performance: Install command will be significantly faster by skipping unchanged files
