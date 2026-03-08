# Change: Fix task manager display in status output

## Why
The `:status` command shows empty values for task manager statistics (`Active Tasks:  (peak: )` and `Timer Events:  total`) because the `tasks` context variable is never populated in the template context.

**Root Cause Analysis:**
1. The template `_taskmanager.mustache` expects `{{tasks.count}}`, `{{tasks.peak_count}}`, and `{{tasks.total_timer_runs}}`
2. `TaskManager.get_task_statistics()` exists and returns this data correctly
3. BUT this data is never added to the template context - neither in `WorkflowContextCache.get_workflow_context()` nor in `TemplateContextCache._build_agent_context()`
4. The comment "# Add task statistics" in `render/cache.py` line 151 was misleading - it only adds OpenSpec context, not general task statistics
5. This has never been properly implemented - the template has always expected this data but it was never wired up

The system has multiple event-driven tasks that should be visible:
- **WorkflowMonitorTask**: Timer + file content events (monitors `.guide.yaml`)
- **OpenSpecTask**: Command, file, directory, timer events (OpenSpec integration)
- **RetryTask**: Timer events (60s interval for retry operations)
- **McpUpdateTask**: One-time timer (checks for updates)
- **ClientContextTask**: File content events (client info caching)

## What Changes
- Add `task_manager.get_task_statistics()` call to populate `tasks` context variable
- Add `tasks` key to the template context (either in workflow context or agent context)
- Ensure task statistics display correctly even when no tasks are active (show `0` instead of empty)

## Impact
- Affected specs: `workflow-monitoring`
- Affected code: `src/mcp_guide/workflow/context.py` OR `src/mcp_guide/render/cache.py`
- Non-breaking: purely additive, fixes display bug
- No changes to task manager logic or template structure
- Makes all registered event-driven tasks visible in status output
