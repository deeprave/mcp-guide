# Change: Project Status Tracking

## Why
The `:status` command currently shows minimal information and doesn't reflect the actual project workflow state. We need a formalized way to track project phases and issue queues through the `.guide` file, making the development workflow visible to both users and agents.

## What Changes
- Formalize `.guide` file format as structured YAML
- Add project status capability to track phases and issue queues
- Update `:status` command to show real workflow information
- Add MCP tools for agents to read and manage `.guide` file
- Make status display conditional on `phase-tracking` project flag

## Impact
- Affected specs: New `project-status` capability
- Affected code:
  - `templates/_commands/status.mustache` - Enhanced status display
  - New MCP tools for `.guide` file management
  - Template context for status information
