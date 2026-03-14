# Implementation Tasks: Fix Task Manager Display

## 1. Restore Task Statistics to Template Context
- [x] 1.1 Add `agent_vars["tasks"] = task_manager.get_task_statistics()` back to `_build_agent_context()` in `src/mcp_guide/render/cache.py`
  - Location: Around line 151, in the "Add task statistics" try block
  - The code was accidentally removed in commit bf23aab
  - Restore the two lines that populate the tasks context variable

## 2. Verify Fix
- [x] 2.1 Run `:status` command and verify task statistics display correctly
  - Should show actual count values instead of empty
  - Should show peak count
  - Should show total timer runs
- [x] 2.2 Verify tasks are listed when active
  - Check that WorkflowMonitorTask, OpenSpecTask, etc. appear in the list
