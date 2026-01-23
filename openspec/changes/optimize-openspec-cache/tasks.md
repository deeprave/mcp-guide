# Tasks: Optimize OpenSpec Cache

## Status: 📋 PLANNED

## Implementation Tasks

### 1. Create OpenSpec cache manager
**File**: `src/mcp_guide/utils/openspec_cache.py` (new)

- [ ] Implement `get_openspec_changes()` - Get cached data if valid
- [ ] Implement `set_openspec_changes(data)` - Cache data with timestamp
- [ ] Implement `invalidate_openspec_changes()` - Clear cache
- [ ] Implement `is_cache_valid(timestamp, ttl)` - Check expiry (15 min default)

### 2. Add cache fields to template context
**File**: `src/mcp_guide/utils/template_context.py`

- [ ] Add `openspec_changes` field for cached JSON data
- [ ] Add `openspec_changes_timestamp` field for cache timestamp
- [ ] Integrate cache manager to populate fields

### 3. Update OpenSpec prompt template
**File**: `src/mcp_guide/templates/_prompts/openspec.mustache`

- [ ] Remove directory listing requests for `openspec/`
- [ ] Remove directory listing requests for `openspec/changes/`
- [ ] Keep command location and version checks
- [ ] Add logic to use cached data when available

### 4. Update :openspec/list command
**File**: Tool handler for `:openspec/list`

- [ ] Check cache first before prompting agent
- [ ] Use cached data if valid
- [ ] Prompt agent to refresh cache on miss
- [ ] Format output from cached data

### 5. Update :openspec/status command
**File**: Tool handler for `:openspec/status`

- [ ] Use cached data to find specific change
- [ ] Avoid running `openspec status` if data in cache
- [ ] Format status from cached data

### 6. Implement cache invalidation
**File**: Cache manager and file watchers

- [ ] Watch `openspec/changes/` directory for modifications
- [ ] Watch `openspec/changes/*/tasks.md` files
- [ ] Invalidate cache on file changes
- [ ] Add manual invalidation instructions to workflow templates

### 7. Update workflow templates
**Files**: Templates that create/modify OpenSpec changes

- [ ] Add cache refresh instruction after change operations
- [ ] Instruct agent to run `openspec list --json` after modifications
- [ ] Send result using `guide_send_file_content`

### 8. Add tests
**File**: `tests/test_openspec_cache.py` (new)

- [ ] Test cache hit (data exists and valid)
- [ ] Test cache miss (data doesn't exist)
- [ ] Test cache expiry (data older than 15 minutes)
- [ ] Test cache invalidation
- [ ] Test commands use cached data

## Verification

- [ ] No directory listing requests in openspec prompt
- [ ] `openspec list --json` cached for 15 minutes
- [ ] `:openspec/list` uses cached data
- [ ] `:openspec/status` uses cached data
- [ ] Cache invalidates on change operations
- [ ] All tests pass
