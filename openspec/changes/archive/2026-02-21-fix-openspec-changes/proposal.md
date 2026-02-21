# Change: Fix OpenSpec Changes Cache Behavior

## Why

The OpenSpecTask timer currently proactively requests the changes list on startup and periodically refreshes it. This is disruptive to users who see unnecessary change gathering when they haven't requested the information. The `:openspec/list` command already handles on-demand requests when the cache is missing, making the proactive fetching redundant.

## What Changes

- Remove proactive changes list request from `on_init()` startup
- Change timer behavior to only invalidate cache, not request new data
- Rely on `:openspec/list` command for on-demand data fetching

## Impact

- Affected specs: `cache-management`
- Affected code: `src/mcp_guide/openspec/task.py` (OpenSpecTask class)
- User experience: Less intrusive, data only fetched when explicitly needed
- No breaking changes: `:openspec/list` command continues to work as before
