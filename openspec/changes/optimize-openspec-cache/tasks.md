# Tasks: Optimize OpenSpec Cache

## Status: ✅ COMPLETE

## Implementation Tasks

### 1. Cache implementation in OpenSpecTask ✅
**File**: `src/mcp_guide/client_context/openspec_task.py`

- [x] Add cache state variables (`_changes_cache`, `_changes_timestamp`)
- [x] Implement `get_changes()` - Returns cached data if valid
- [x] Implement `is_cache_valid(ttl)` - Check expiry (1 hour TTL)
- [x] Cache population in `handle_event()` for `.openspec-changes.json`
- [x] Add filter flags: `is_draft`, `is_done`, `is_in_progress`

### 2. Expose cache in template context ✅
**File**: `src/mcp_guide/utils/template_context_cache.py`

- [x] Add `changes` field to openspec context
- [x] Populate from `openspec_task_subscriber.get_changes()`

### 3. Remove directory listing ✅
**Files**: Templates and OpenSpecTask

- [x] Delete `openspec-changes-check.mustache` template
- [x] Update `openspec-project-check.mustache` to request file content only
- [x] Remove `_check_project_structure()` method
- [x] Remove `_handle_changes_listing()` method
- [x] Simplify project detection to file-based check

### 4. Update :openspec/list command ✅
**File**: `src/mcp_guide/templates/_commands/openspec/list.mustache`

- [x] Check cache first before prompting
- [x] Add filter support: `--draft`, `--done`, `--prog`
- [x] Prompt to refresh cache if empty/stale
- [x] Re-render template after cache refresh
- [x] Fix excessive newlines in filtered output

### 5. Update :openspec/status command ✅
**File**: `src/mcp_guide/templates/_commands/openspec/status.mustache`

- [x] Check cache for change existence
- [x] Validate change exists before status command
- [x] Prompt to refresh cache if needed

### 6. Implement cache invalidation ✅
**Files**: Workflow templates

- [x] `archive.mustache` - Refresh after archive
- [x] `change/new.mustache` - Refresh after creating change
- [x] `init.mustache` - Refresh after initialization

### 7. Add tests ✅
**File**: `tests/test_openspec_task.py`

- [x] Test cache population with filter flags
- [x] Test `get_changes()` returns None when no cache
- [x] Test `is_cache_valid()` returns False when no cache
- [x] Test `is_cache_valid()` returns True when fresh
- [x] Test `is_cache_valid()` returns False when stale
- [x] Test timer event skips reminder before start delay
- [x] Update existing tests for new cache-only behavior

## Verification ✅

- [x] No directory listing in openspec-project-check template
- [x] `openspec list --json` cached for 1 hour
- [x] `:openspec/list` uses cached data with filters
- [x] `:openspec/status` uses cached data
- [x] Cache invalidates after mutations
- [x] All 34 OpenSpec tests pass
- [x] Type checks pass (mypy)
- [x] Linting passes (ruff)
- [x] Pre-commit checks pass
