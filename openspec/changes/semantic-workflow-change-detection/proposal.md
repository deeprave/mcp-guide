# Semantic Workflow Change Detection

**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium

## Why

Currently, when workflow file content is received and parsed, the system returns redundant information (echoing back the same content the agent just sent). This provides no semantic value and misses opportunities to provide meaningful context about what actually changed.

The agent needs to understand:
- What specific aspects of the workflow state changed (phase, issue, tracking, description, queue)
- Phase transition rules when phases change (critical for proper behavior)
- Context about what changed from/to for better decision making

This is particularly important for phase changes, where agents often misunderstand the rules (e.g., refusing to make changes during review phase when review includes responding to feedback).

## What Changes

- Replace redundant content echo-back with semantic change detection
- Implement workflow state comparison logic to detect specific changes
- Generate contextual change events with from/to information
- Include phase-specific rules when phase transitions occur
- Support multiple change types in a single workflow update

### Change Types to Detect
- **Phase transitions**: Include relevant phase rules from templates
- **Issue changes**: Track what issue was changed from/to or cleared
- **Tracking changes**: Monitor tracking field updates
- **Description changes**: Note when description is added/modified/removed
- **Queue changes**: Detect items added/removed from queue

## Impact

- Affected specs: workflow-monitoring
- Affected code:
  - `src/mcp_guide/workflow/tasks.py` (WorkflowMonitorTask)
  - `templates/_workflow/` (new change detection templates)
- **BREAKING**: Changes the structure of workflow monitoring responses
