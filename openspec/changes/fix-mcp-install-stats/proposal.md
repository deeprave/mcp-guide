# Change: Fix Install Command to Implement Smart Update Strategy

## Why
**CRITICAL BUG**: The `install` command does not implement the Smart Update Strategy specified in the installation spec. It blindly copies all files without:
- Checking if files are unchanged (wastes time)
- Detecting user modifications
- Preserving user changes via diff/patch
- Creating backups when patches fail

**Spec Requirements (NOT IMPLEMENTED):**
- "Smart Update Strategy" - SHALL handle user modifications intelligently
- "File modified by user" - SHALL compute diff and apply to new version
- "Patch application fails" - SHALL backup current file and warn user
- "File identical to new version" - SHALL skip file
- "Async File Comparison" - SHALL compare files using SHA256

**Current State:**
- `install_file()` - NO comparison, NO diff/patch, always copies (VIOLATES SPEC)
- `smart_update()` - Has full logic ✓ (used by update command)
- Tests - NO tests for install_file() smart update behavior
- E2E tests - NO tests verifying user modifications are preserved

**Additional Issues:**
- Spec has illogical scenario "File unchanged from original → Update without backup" (why update unchanged files?)
- Both install and update commands report inaccurate statistics

## What Changes

### 1. Implement Smart Update Strategy in install_file()
- Check if destination file exists
- Compare with original from `_installed.zip` (if available)
- **If file doesn't exist**: Install new file
- **If current = new version (SHA256)**: Skip (no changes needed)
- **If archive exists**:
  - **If current = original**: Update to new version (no user changes)
  - **If current ≠ original**: User modified file
    - Compute diff between original and current
    - Apply diff to new version
    - If patch succeeds: Keep patched result
    - If patch fails: Backup as `orig.<filename>`, install new, warn user
- **If no archive exists**:
  - **If current = new version**: Skip (unchanged)
  - **If current ≠ new version**: Backup as `orig.<filename>`, install new, warn user
  - Cannot distinguish user modifications from template changes without archive

### 2. Fix Installation Spec
Create spec delta to correct illogical scenario:
- **REMOVE**: "File unchanged from original → Update without backup"
- **ADD**: "File unchanged from original and different from new → Update to new version"
- Logic: Only update if new version differs from current

### 3. Accurate Statistics
- Track operations: installed/updated/patched/skipped/conflicts
- Report actual operations performed, not total file count

### 4. Add Comprehensive Tests
- Unit tests for all smart update scenarios
- E2E tests verifying user modifications preserved
- Test backup creation on patch failure

### 5. Add --quiet Flag
- Support `-q`/`--quiet` to suppress non-error output
- Still show warnings about conflicts/backups

## Impact
- Affected specs: `installation` (fixing bug + correcting illogical scenario)
- Affected code:
  - `src/mcp_guide/installer/core.py` - `install_file()` complete rewrite
  - `src/mcp_guide/scripts/mcp_guide_install.py` - statistics, quiet flag
  - `tests/unit/installer/test_core.py` - Add comprehensive tests
  - `tests/unit/scripts/test_mcp_guide_install.py` - Add E2E tests
- Breaking: None (fixes bug, improves correctness)
- Performance: Significantly faster by skipping unchanged files
- User Experience: Preserves user modifications instead of overwriting
