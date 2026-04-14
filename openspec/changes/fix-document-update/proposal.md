# Change: fix-document-update

## Why

The current document update workflow has three behavior gaps.

First, the global `autoupdate` feature flag is currently opt-in. When the flag
is unset, startup update prompting is disabled. The desired behavior is the
inverse: startup prompting should be enabled by default, and only an explicit
`false` should suppress it.

Second, the startup update prompt is currently queued as a normal instruction.
That means the agent can fail to act on it without any follow-up. The desired
behavior is to queue an acknowledged instruction so the existing retry/reminder
machinery keeps prompting until the update is executed or otherwise
acknowledged.

Third, the update path has drifted in two ways from the intended model. The
`update_documents` tool currently requires a bound project even though it only
needs global configuration to resolve docroot, and the installer keeps files
that were removed from the upstream document set even when the local copies are
still unchanged. That leaves stale documents behind after upgrades.

## What Changes

- Change `autoupdate` semantics so an unset flag is treated as enabled and only
  an explicit `false` disables startup update prompting
- Register `autoupdate` with the standard boolean normaliser so accepted
  boolean-like values are canonicalised consistently
- Change `McpUpdateTask` to queue the startup update prompt as an acknowledged
  instruction with reminder/retry behavior
- Make `update_documents` callable without a bound project, using session/global
  docroot configuration only
- Extend document update behavior to delete files that existed in the previous
  installed document set but no longer exist in the new version, but only when
  the local file is unchanged from the previously installed original
- Leave parent directories untouched when removed files are deleted

## Impact

- Affected specs:
  - `workflow-flags`
  - `task-manager`
  - `tool-infrastructure`
  - `installation`
- Likely affected implementation:
  - `src/mcp_guide/tasks/update_task.py`
  - `src/mcp_guide/task_manager/manager.py`
  - `src/mcp_guide/tools/tool_update.py`
  - `src/mcp_guide/installer/core.py`
  - `src/mcp_guide/templates/_system/_update.mustache`
  - tests covering update task, tool behavior, and installer update flows
- No new external dependencies expected
