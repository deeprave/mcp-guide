## Why

Workflow commands are useful guidance even when a project has no enabled workflow. Gating them on workflow state hides generally applicable phase principles and entangles general guidance with Guide-specific state-management instructions.

## What Changes

- Keep workflow phase commands discoverable and usable without an enabled workflow.
- Treat enabled workflow state as optional add-in content rather than a prerequisite for command availability.
- Curate command text so it presents general phase principles while reserving Guide-specific transitions, state updates, and tool actions for the optional workflow section.

## Capabilities

### New Capabilities

- `workflow-command-guidance`: Provide phase-oriented workflow commands with general guidance and optional state-aware additions.

### Modified Capabilities

- `workflow-templates`: Render workflow-specific command details conditionally without suppressing the command itself.

## Impact

- Workflow command templates, frontmatter requirements, rendering context, command discovery, and tests.
