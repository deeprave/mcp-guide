# Design

## Context

See [proposal.md](proposal.md) for motivation. A linked worktree shares the repository project's persisted configuration, including its resolved basename-only `workflow-file` setting, but its session and workflow file are distinct. `.guide.yaml` is only the default when that flag is unset. The root agent creates the target checkout and configured workflow file before the child creates its fresh Guide interaction. That child can run in a separate Guide process, so process-local label state cannot be its source of truth.

## Goals / Non-Goals

**Goals:**

- Establish one durable label handshake: the `worktree` key in the linked checkout's effective configured workflow file.
- Let a child session process that file even when its shared project does not enable workflow.
- Preserve the shared project's configuration and workflow settings.
- Make root-originated `_worktree/new` and `_worktree/use` initialise the child before handoff.

**Non-Goals:**

- Persisting a worktree-to-label registry in project configuration.
- Inferring labels from a checkout path or directory name.
- Enabling workflow for the root session or other sessions of a project that has not selected it.
- Supporting creation of a linked worktree from another linked worktree.

## Decisions

### Workflow file is the label authority

`set_project` binds the project root and checkout path only. For a linked checkout it leaves the label unresolved until the first valid local configured workflow file is received; it never generates a label. The workflow monitor adopts the file's `worktree` value and rejects later conflicting values.

This replaces a process-local label map, which cannot reliably cross a fresh child interaction or server process. It also avoids using names derived from a directory, which are neither stable nor meaningful.

### Root handoff initialises all labels

Only a root-bound session may use `_worktree/new`. It allocates a label, creates the sibling checkout, and writes the parent's effective configured workflow file there with that label before directing a child to bind it. `_worktree/use` follows the same initialisation path for a discovered existing checkout that lacks that configured file or label.

The child instruction includes the path, label, and an immediate read of its effective configured workflow file. The file confirms the label used to select `worktrees.<label>` from the client-owned handover document.

### Linked sessions use an effective minimum workflow configuration

When the shared project's workflow setting is disabled, a linked-worktree session gets a local effective workflow configuration containing `discussion` and `implementation` (normalised using the existing workflow rules). This activates its monitor solely to receive and process its local workflow file. The override remains on the session/task; it does not call configuration persistence or publish a project flag update.

When the project already enables workflow, the linked session continues using the shared configured sequence.

## Risks / Trade-offs

- [A child binds before its configured workflow file is available] → leave its label unresolved, request that file, and do not invent a replacement.
- [An external checkout has no configured workflow file] → `_worktree/use` allocates and writes a label before child handoff.
- [A malformed or conflicting workflow file] → preserve the existing session state and return the existing validation failure rather than accepting an ambiguous label.

## Migration Plan

Existing labelled worktrees continue to work: their first configured workflow-file receipt adopts the existing label. Existing unlabelled checkouts are initialised through `_worktree/use`. Rolling back restores the prior binding behaviour but does not require configuration migration because labels are not persisted by Guide.
