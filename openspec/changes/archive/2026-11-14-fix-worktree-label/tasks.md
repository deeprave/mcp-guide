# Tasks

## 1. Linked-worktree binding and monitoring

- [x] 1.1 Stop linked-worktree session binding from allocating a label; leave it unresolved until the effective configured workflow file supplies `worktree`, with behavioural coverage for adoption and conflicting labels.
- [x] 1.2 Normalise the effective workflow flag for linked-worktree sessions to the minimum phases when the root agent's persisted workflow flag is disabled, without persisting or publishing a project-flag change.
- [x] 1.3 Centralise linked-worktree detection on `Session.is_worktree()`.

## 2. Root handoff initialisation

- [x] 2.1 Update `_worktree/new` to permit root-bound sessions only and initialise the new checkout's effective configured workflow file with its allocated label before child handoff, including coverage.
- [x] 2.2 Update `_worktree/use` to initialise an existing unlabelled checkout's effective configured workflow file with its established handoff label before child handoff, including coverage.
- [x] 2.3 Update child handoff instructions to require an immediate read of the effective configured workflow file before workflow or handover-context operations.
- [x] 2.4 Let `_worktree/use` select a fresh inventory path when no label is supplied, and initialise an external unlabelled checkout from the root session.
