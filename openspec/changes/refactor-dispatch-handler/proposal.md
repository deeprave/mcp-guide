# Change: Refactor Event Dispatch Handler

## Why
The current `dispatch_event` implementation has mixed concerns and design flaws:
- Returns either `Result` or `dict`, mixing return types
- Only returns result from first handler, ignoring other subscribers
- Echoes received data pointlessly (directory listings, file content, paths)
- Template rendering responsibility unclear

## What Changes
- Separate concerns between event dispatch and result handling
- Return structured dict with all handler results, not just one
- Add dispatcher function above `dispatch_event` for template rendering
- Standardise return format with processed count and optional template info

## Impact
- Affected specs: task-manager, event-handling
- Affected code:
  - `src/mcp_guide/task_manager/manager.py` (dispatch_event, new dispatcher)
  - Event handlers that return Result objects
  - Tools that call dispatch_event
