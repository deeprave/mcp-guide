# Change: Add Startup Collection Support

## Why
When a project loads, agents need immediate access to critical startup instructions. Currently, there's no mechanism to automatically inject high-priority instructions that guide the agent's initial context and behaviour for a project.

## What Changes
- Add `on_project()` event that triggers when a project loads
- Check for a "startup" collection and inject its content as highest-priority instruction
- Ensure startup instructions are expressed as "SHOULD NEVER BE IGNORED"
- Update workflow message templates to also use "SHOULD NEVER BE IGNORED" phrasing

## Impact
- Affected specs: project-management, instruction-queue
- Affected code: 
  - `src/mcp_guide/guide.py` (GuideMCP.on_init chain)
  - `src/mcp_guide/task_manager/manager.py` (instruction queue priority)
  - Workflow message templates
