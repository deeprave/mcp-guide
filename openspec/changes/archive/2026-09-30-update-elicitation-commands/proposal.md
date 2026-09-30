# Proposal

## Why

Guide now asks for handoff context through the `handoff-context` feature flag, so the separate `:handoff` read/write command is redundant. Workflow review, phase, and reset still make the agent infer a target, a phase, or a git action instead of offering the choices that belong to the current repository and the enabled workflow.

## What Changes

- **BREAKING**: Retire the `:handoff` command and its `save-context` / `restore-context` aliases. Proactive handoff stays on the `handoff-context` feature flag. `agent.has_handoff` remains the separate-execution capability.
- `workflow/review` asks for one current-repository comparison when no target is supplied: uncommitted work against `HEAD`, the current branch against the default branch, a named branch against the default branch, or a pull request number in this repository. A supplied URI target skips the question.
- `workflow/phase` asks only when no phase was given. The choices are the phases enabled by the current `workflow` project flag, excluding the active phase. A supplied phase is still rejected when it is not enabled.
- `workflow/reset` asks the calling agent to inspect its own repository. It does nothing on the default branch. A dirty worktree on another branch asks whether to stash, reset the workflow, and restore the stash. Declining leaves the workflow file unchanged. A clean worktree on another branch continues the existing workflow-file reset.
- Tests that assert the literal content of production templates are removed. Behaviour is tested without binding the suite to template wording.

## Capabilities

### New Capabilities

- `workflow-commands`: Current-repository review targets, enabled-phase selection, and reset git guards for the workflow commands.

### Modified Capabilities

- `help-template-system`: Remove the requirement that `:handoff` support explicit read and write workflows.
- `prompt-infrastructure`: Remove the handoff `save-context` and `restore-context` alias scenarios. Generic alias query behaviour stays.
- `mcp-resources-guide-scheme`: Remove the handoff `save-context` and `restore-context` guide URI scenarios. Generic alias URI behaviour stays.
- `test-quality`: Tests must not assert the literal content of production templates.

## Impact

- Command templates under `src/mcp_guide/templates/_commands/`, including removal of `_commands/handoff.mustache`.
- Command input preparation before elicitation for enabled workflow-phase choices. Reset repository checks remain in the calling agent's checkout.
- Living specs listed above. The `handover-context` flag, startup handoff prompt, onboarding, OpenSpec commands, and `agent.has_handoff` stay as they are.
- Tests that currently render production command templates and assert their wording, including workflow phase, review, and reset template assertions.
- Linear UT-424 tracks this change.
