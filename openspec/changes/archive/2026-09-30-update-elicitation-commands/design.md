# Design

## Context

See proposal.md for why the handoff command and the three workflow commands change. Elicitation forms are declared in command frontmatter and resolved before rendering. Enum values in that frontmatter are static. The enabled workflow phases and the git worktree are known only when a command runs.

## Goals / Non-Goals

**Goals:**

- Fill the phase choice from the enabled workflow phases, excluding the active phase, before the input request is issued.
- Keep reset repository inspection and stash consent in the calling agent's checkout.
- Keep review choices static because they do not depend on repository contents beyond the current repository.

**Non-Goals:**

- Changing the `workflow-review` skill, onboarding, or OpenSpec commands.
- Changing `agent.has_handoff` or the `handoff-context` flag implementation.
- Adding a general elicitation feature for arbitrary dynamic enums outside these workflow commands.

## Decisions

### Retire the handoff command by deleting its template

The command is discovered from `_commands/handoff.mustache`. Removing that file removes the entrypoint and the aliases that existed only for it. The living alias requirements keep the generic `project?verbose` behaviour and drop the handoff-specific scenarios.

Alternative: leave the command as a thin pointer at the feature flag. Rejected because the flag already delivers startup guidance, and a second entrypoint keeps the old read/write contract alive.

### Specialise workflow forms before generic elicitation resolution

Command execution prepares the effective forms, then resolves elicitation. A phase property marked as coming from the workflow configuration is replaced with the enabled phase names other than the active phase. A positional phase skips that form. When no other phase remains, the form is omitted and the command shows the current phase.

Alternative: a static enum of every known phase name. Rejected because a project flag can disable phases, and the active phase must not be offered again.

### Keep reset Git operations in the calling agent

The server cannot assume access to the calling agent's checkout. `workflow/reset` therefore does not
inspect Git or issue a stash elicitation form. Its rendered guidance requires the calling agent to
determine the default branch and worktree state in its own repository, run completion checks before
stashing, obtain explicit stash consent when needed, restore the stash unconditionally, and only then
update the workflow file. The same guards apply to `reset/<issue-id>`.

### Test behaviour without production template text

Command-input preparation and git inspection are tested with fixtures and temporary repositories. Tests that render production command templates and assert their wording are removed, including workflow phase, review, and reset assertions.

## Risks / Trade-offs

- [The server cannot see the client worktree] → Reset always uses agent-side repository checks and does not attempt server inspection.
- [Removing `:handoff` breaks existing invocations] → The feature flag is the replacement. There is no alias left that routes to the deleted command.

## Migration Plan

Remove the handoff command template and the requirements that mention it. Existing `handoff-context` configuration continues to request startup handoff guidance. Rollback is restoring the command template and the removed requirement text.

## Open Questions

None.
