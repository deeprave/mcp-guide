# Proposal

## Why

Linked-worktree sessions currently mint a new label during `set_project`, before they receive the workflow file that already identifies the worktree. This leaves the child session, its workflow state, and its handover context referring to different labels. A linked worktree also cannot process its workflow file when its shared project's workflow flag is unset.

## What Changes

- Stop session binding from allocating a linked-worktree label; obtain the label from that worktree's workflow file instead.
- Require root-originated worktree handoff to create or initialise the target's effective configured `workflow-file` and label before a child binds it.
- Give a linked-worktree session a local minimum workflow capability when the shared project has workflow disabled, without changing the shared project configuration.
- Instruct each child worktree agent to read its local workflow file immediately so it can adopt the label and use the corresponding handover entry.
- Allow `_worktree/use` to initialise an existing unlabelled worktree with a newly allocated label and workflow file before handoff.
- Reject new-worktree creation from a non-root linked-worktree session.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `worktree-support`: make workflow-file labels the sole source of linked-worktree identity and define root-only handoff initialisation.
- `workflow-monitoring`: activate local monitoring for a linked worktree when it needs to receive its initial workflow file despite shared workflow being disabled.

## Impact

- Affects worktree session binding, worktree command templates and workflow monitoring.
- Keeps durable project flags shared and unchanged; the minimum linked-worktree workflow capability is session-local.
- Does not add dependencies or change the public configuration identity of a linked worktree.
