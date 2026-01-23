# Tasks: Remove Profile Metadata Tracking

## Status: 📋 PLANNED

## Implementation Tasks

### 1. Remove metadata tracking from Profile model
**File**: `src/mcp_guide/models/profile.py`

- [ ] Remove lines 150-160 that track applied profiles in metadata
- [ ] Profile.apply_to_project() should only add categories and collections

### 2. Remove metadata display
**File**: `src/mcp_guide/models/__init__.py`

- [ ] Remove lines 161-164 that add applied_profiles to formatted output
- [ ] format_project_data() should not include applied_profiles

### 3. Remove idempotency check based on metadata
**File**: `src/mcp_guide/tools/tool_project.py`

- [ ] Remove lines checking `applied_profiles` metadata in internal_use_project_profile()
- [ ] Idempotency is already handled by checking if categories/collections exist

### 4. Update tests
**Files**: `tests/unit/test_profile.py`, `tests/integration/test_profile_application.py`

- [ ] Remove assertions checking for applied_profiles metadata
- [ ] Tests should verify categories and collections exist, not metadata

## Verification

- [ ] All tests pass
- [ ] Profiles still apply correctly
- [ ] No references to applied_profiles remain in codebase
