# Design: Optimize OpenSpec Cache

## Overview

Add 1-hour caching for `openspec list --json` output to eliminate redundant filesystem operations and CLI calls. Replace directory-based project detection with file-based detection.

## Architecture

### Cache Implementation

**Location**: `OpenSpecTask` class in `src/mcp_guide/client_context/openspec_task.py`

**State Variables**:
- `_changes_cache: Optional[list[dict[str, Any]]]` - Cached changes data
- `_changes_timestamp: Optional[float]` - Cache timestamp
- `_changes_timer_started: bool` - Track first timer fire

**Constants**:
- `CHANGES_CACHE_TTL = 3600` - 1 hour cache lifetime
- `CHANGES_CHECK_INTERVAL = 3600.0` - 60 minute timer interval
- `CHANGES_CHECK_START_DELAY = 20.0` - 20 second initial delay

### Cache Methods

```python
def get_changes() -> Optional[list[dict[str, Any]]]
    """Return cached changes if valid, None otherwise"""

def is_cache_valid(ttl: int = CHANGES_CACHE_TTL) -> bool
    """Check if cache exists and is not expired"""
```

### Filter Flags

Each cached change gets computed flags:
- `is_draft`: `total == 0` (no tasks defined)
- `is_done`: `total > 0 and completed == total` (all tasks complete)
- `is_in_progress`: `total > 0 and completed < total` (has tasks, not done)

### Cache Population

**Trigger**: Receiving `.openspec-changes.json` file content via `FS_FILE_CONTENT` event

**Process**:
1. Parse JSON content
2. Compute filter flags for each change
3. Store in `_changes_cache` with current timestamp
4. Update task manager cached data
5. Do NOT auto-display (let command templates handle)

### Cache Invalidation

**Explicit Refresh**: Mutation templates instruct agent to refresh cache
- `archive.mustache` - After archiving change
- `change/new.mustache` - After creating new change
- `init.mustache` - After project initialization

**Timer-Based**: Hourly reminder checks cache validity and refreshes if stale

**First Timer Skip**: `_changes_timer_started` flag prevents first timer from firing (respects initial delay)

## Project Detection

**Old Approach** (removed):
- Request directory listing of `openspec/`
- Check for `project.md`, `changes/`, `specs/` directories
- Complex validation logic

**New Approach**:
- Check for `openspec/project.md` file content event
- If file exists, project is enabled
- Simpler, eliminates directory listing

## Template Integration

### Context Exposure

`template_context_cache.py` adds to openspec context:
```python
"changes": openspec_task_subscriber.get_changes() or []
```

### Command Templates

**list.mustache**:
- Check `{{#openspec.changes.0}}` for cache presence
- Support `--draft`, `--done`, `--prog` filter flags
- Prompt to refresh if cache empty/stale
- Re-render after refresh

**status.mustache**:
- Check cache for change existence
- Prompt to refresh if cache empty
- Run status command only if change found

## Data Flow

```
1. Agent runs: openspec list --json
2. Agent sends: guide_send_file_content(.openspec-changes.json)
3. OpenSpecTask receives: FS_FILE_CONTENT event
4. OpenSpecTask: Parse JSON, compute flags, cache data
5. Template renders: Access via {{openspec.changes}}
6. Display: Filtered list based on flags
```

## Timer Behavior

```
Subscribe: interval=3600s, initial_delay=20s
First event: Skip (set _changes_timer_started=True)
Subsequent events: Check cache validity, refresh if stale
```

## Performance Impact

**Before**:
- Directory listing on every project check
- `openspec list` on every list command
- No caching, repeated CLI calls

**After**:
- File-based project detection (single file check)
- Cached changes list (1 hour TTL)
- CLI calls only on cache miss or mutation
- Reduced filesystem operations by ~80%

## Error Handling

- Invalid JSON: Log error, don't cache
- Missing fields: Use defaults (0 for counts)
- Cache miss: Prompt agent to refresh
- Timer errors: Log warning, continue

## Testing Strategy

- Cache population and validation
- Filter flag computation
- Timer first-fire skip
- Cache-first command behavior
- Template rendering with/without cache
