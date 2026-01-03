# Change: Project Status Tracking

## Why
The `:status` command currently shows minimal information and doesn't reflect the actual project workflow state. We need a formalized way to track project phases and issue queues, making the development workflow visible to both users and agents.

## What Changes
This change is split into multiple sub-specifications for manageable implementation:

1. **workflow-flags**: Rename and enhance project flags for workflow management
2. **workflow-context**: Add workflow variables to template context
3. **workflow-fsm**: Implement WorkflowManager FSM for agent coordination
4. **workflow-templates**: Add frontmatter conditional rendering
5. **workflow-monitoring**: Add automatic state file monitoring

## Impact
- Affected specs: Multiple new workflow-related capabilities
- Affected code: Template system, MCP tools, project flags, status display
- Breaking changes: Flag names changed from `phase-*` to `workflow-*`
