# Workflow Support

mcp-guide provides MCP-assisted workflow support for development, giving users complete control over how AI agents participate in the development process.

## Overview

Workflow support enables structured development phases with configurable agent behaviour. Users can choose from no workflow assistance (default), minimal assistance, or full multi-phase workflows with consent controls.

## Workflow Phases

| Phase | Purpose |
|-------|---------|
| discussion | Initial problem analysis and requirements gathering |
| planning | Implementation plan creation and review |
| implementation | Code changes and feature development |
| check | Testing and validation |
| review | Final review before completion |

## State File

Workflow state is tracked in `.guide.yaml` (configurable via `workflow-file` flag):

```yaml
phase: planning
issue: add-feature-x
plan: .todo/feature-x-plan.md
tracking: JIRA-123
description: Optional context
queue:
  - next-issue
  - another-issue
```

**Fields:**
- `phase`: Current workflow phase (required)
- `issue`: Current issue ID or path (optional)
- `plan`: Path to implementation plan (optional)
- `tracking`: External tracker reference (optional)
- `description`: Phase context or sub-phase info (optional)
- `queue`: Queued issues in priority order (optional)

## Configuration

### The `workflow` Feature Flag

This feature flag, normally set at the project level, controls which phases are enabled. It may be:

**Boolean:**
- `false` / absent: No MCP-assisted workflow (default)
- `true`: Enables all 5 phases

**List:**
- Custom phase selection (if enabled, `discussion` and `implementation` are mandatory)
- Example: `[discussion, implementation]` - Minimal workflow
- Example: `[discussion, implementation, review]` - Common workflow

### The `workflow-consent` Feature Flag

`workflow-consent` controls automatic phase transitions. It is also a multi-type flag:

**Boolean:**
- `false` / absent: Agent transitions automatically between phases
- `true`: Default consent stops at critical transitions
  - Requires consent before entering implementation (prevents enthusiastic agents from making changes)
  - Requires consent before exiting review (prevents automatic mode change before review is finalised)

**Dict:**
- Custom per-phase consent configuration
- Keys: Phase names
- Values: List of `'entry'` and/or `'exit'`

**Consent types:**
- `entry`: Require explicit consent to enter the phase
- `exit`: Require explicit consent to exit the phase

If `workflow-consent` is configured with at least one phase, the default configuration for every phase is not to require consent on either entry or exit unless overridden.

## Workflow Commands

Tracking workflow status is an important aspect of how the MCP operates. When transitioning between phases it will send certain instructions to the agent in order to keep it appraised of what actions are allowed or prevented. Unfortunately, agents are non-deterministic and will sometimes "forget" to send updates to the MCP. The MCP server, however, will periodically send reminders on the back of other responses, and unless the agent is being particularly stubborn, it should eventually comply.

Frequent use of workflow commands will increase the opportunity of the mcp sending these instructions. When workflow is enabled, additional workflow prompt commands become available, many of which have shortcuts or aliases. Use `@guide :help` for more information.

**@guide :workflow/show** _(:show)_
Displays the current workflow status and other details. This should directly correspond with the content of the workflow file (`.guide.yaml`) unless the mcp is not being updated by the agent.

**@guide :workflow/issue** _(:issue)_
Manage or change the current workflow issue, description, tracking and transition to next

**@guide :workflow/discuss** _(:discuss)_
Requests return to discussion mode, optionally switch to a different issue if specified

**@guide :workflow/reset** _(:reset)_
Marks the current issue as complete and resets to discussion (shortcut).
Certain conditions must be met:
  - there are no staged/uncommitted changes
  - the current branch must be `main`

**@guide :workflow/phase** _(:phase)_
Requests transition to a specific provided workflow phase

**:workflow/check** _(:check)_
Run all code checks for changes according to test and code quality checks for the project.

**:workflow/review** _(:review)_
Delegate a review to a guide-review agent.
If delegates are not supported by the agent, then `@guide code-review` will do the same thing in the foreground.

**:workflow/implement** _(:implement)_
Explicitly requests commencement of the implementation phase.

**:workflow/plan** _(:plan)_
Explicitly requests creating an implementation plan for the current change.

## Workflow Template Context

If workflow is enabled, the current workflow state is available in content templates via `{{workflow.*}}` variables.
Note that this relies on the agent updating the mcp of the current state via the internal `send_file_content` tool.

- `{{workflow.phase}}` - Current phase name
- `{{workflow.issue}}` - Current issue ID or path
- `{{workflow.plan}}` - Implementation plan path
- `{{workflow.tracking}}` - External tracker reference
- `{{workflow.description}}` - Phase context
- `{{workflow.queue}}` - Queued issues list
