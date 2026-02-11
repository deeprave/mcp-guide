# Change: Refactor Event Dispatch Handler

## Why
The current `dispatch_event` implementation has mixed concerns and design flaws:
- Returns either `Result` or `dict`, mixing return types
- Only returns result from first handler, ignoring other subscribers
- Echoes received data pointlessly (directory listings, file content, paths)
- Template rendering responsibility unclear and type-specific

## What Changes
- Standardise `dispatch_event` to return list of `EventResult` objects
- Create `EventResult` composite object with:
  - `result: bool` (success/failure)
  - `message: Optional[str]` (simple string result)
  - `rendered_content: Optional[RenderedContent]` (rendered template)
- Simplify Result construction:
  - Use default instruction for success/failure
  - Override with `rendered_content.instruction` if present
  - Set `value` to `rendered_content.content` if rendered

## Impact
- Affected specs: task-manager, event-handling
- Affected code:
  - `src/mcp_guide/task_manager/manager.py` (dispatch_event, EventResult)
  - Event handlers that return results
  - Tools that call dispatch_event
- Benefits:
  - Handlers don't deal with template types (openspec, workflow, etc.)
  - Cleaner separation: handlers render if needed, otherwise return simple result
  - Consistent return format across all handlers
