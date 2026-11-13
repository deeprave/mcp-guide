# Tasks

## 1. Linked-worktree binding and monitoring

- [x] 1.1 Stop linked-worktree session binding from allocating a label; leave it unresolved until the effective configured workflow file supplies `worktree`, with behavioural coverage for adoption and conflicting labels.
- [x] 1.2 Give linked-worktree sessions a local minimum workflow configuration when their shared project disables workflow, without persisting or publishing a project-flag change, with behavioural coverage.

## 2. Root handoff initialisation

- [x] 2.1 Update `_worktree/new` to permit root-bound sessions only and initialise the new checkout's effective configured workflow file with its allocated label before child handoff, including coverage.
- [x] 2.2 Update `_worktree/use` to initialise an existing unlabelled checkout's effective configured workflow file with its established handoff label before child handoff, including coverage.
- [x] 2.3 Update child handoff instructions to require an immediate read of the effective configured workflow file before workflow or handover-context operations.
