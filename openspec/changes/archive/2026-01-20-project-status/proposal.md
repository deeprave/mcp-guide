# Change: Project Status Tracking

## Why
The `:status` command currently shows minimal information and doesn't reflect the actual project workflow state. We need a formalized way to track project phases and issue queues, making the development workflow visible to both users and agents.

## What Changes
This change is split into multiple sub-specifications for manageable implementation:

1. **workflow-flags**: ✅ COMPLETED - Rename and enhance project flags for workflow management
2. **workflow-context**: ✅ COMPLETED - Add workflow variables to template context
3. **workflow-fsm**: ✅ COMPLETED - Implement WorkflowManager FSM for agent coordination
4. **workflow-templates**: ✅ COMPLETED - Add frontmatter conditional rendering
5. **refactor-task-pubsub**: 🔄 IN PROGRESS - Replace FSM callback registration with pub/sub system featuring EventType bitflags, timer events, and weak reference management

## Impact
- Affected specs: Multiple new workflow-related capabilities ✅ IMPLEMENTED
- Affected code: Template system, MCP tools, project flags, status display ✅ IMPLEMENTED
- Breaking changes: Flag names changed from `phase-*` to `workflow-*` ✅ COMPLETED

## Implementation Status
**Overall Progress: ~90% Complete**
- Core workflow functionality is operational
- State file monitoring and agent coordination working
- Template system integration complete
- Only pub/sub refactoring remains for improved event system reliability
