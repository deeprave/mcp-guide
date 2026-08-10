## Context

Workflow command templates currently use workflow requirements as availability gates. Their content combines universal phase practice with Guide-specific state and transition instructions.

## Goals / Non-Goals

**Goals:**
- Make phase commands useful without workflow configuration.
- Add state-aware workflow details only when workflow is enabled and applicable.

**Non-Goals:**
- Changing the project's workflow phases or consent model.

## Decisions

- Remove workflow availability gates from general workflow commands and use conditional blocks for add-in content.
- Retain general phase principles in the base template and move Guide URI, state-file, transition, and task-management instructions into workflow blocks.

## Risks / Trade-offs

- [Less specific output without workflow] → retain concise, actionable general phase guidance.
- [Conditional omissions] → test both enabled and disabled rendering paths for every command.
