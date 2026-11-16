# Proposal

## Why

The default handoff context can be deliberately shared by separate projects, for example through a `.todo` symlink. Each primary checkout currently writes `worktrees.root`, so sibling projects overwrite one another's handoff state despite having independent project identities.

## What Changes

- **BREAKING** Namespace structured handoff entries by Guide project name before their worktree label: `projects.<project-name>.worktrees.<worktree-name>`.
- Support a shared handoff document only where each participating Guide project has a distinct configured project name; projects with the same name are not supported as separate namespaces.
- Keep `root` as the primary checkout's worktree label only; it is no longer the top-level identity for a handoff entry.
- Update handoff guidance, locking and merge instructions so an agent updates only its own project/worktree entry, preserves sibling projects and genuine global top-level data, and can supply complete agent-agnostic handoff context beyond bookkeeping fields.
- Preserve legacy `worktrees.<name>` data while merging applicable current-project entries into its project namespace, retaining the state with the newer timestamp on conflict. Treat legacy root-level handoff state as the current project's `root` context, except for genuinely global data such as shared todo items or instructions. Keep this temporary migration guidance to one concise, complete paragraph without examples or embellishment.
- Ensure review requests do not update handoff context. They may only change workflow state when its phase is not already `review`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `worktree-support`: namespace shared handoff state by project and worktree so separately configured projects can safely share a context file.

## Impact

- Handoff-context rendering and client-side merge instructions
- Worktree handoff, allocation, resume, and lock guidance
- Structured handoff documents that use the current `worktrees.<name>` layout
