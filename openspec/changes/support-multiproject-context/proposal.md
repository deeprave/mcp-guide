# Proposal

## Why

The default handoff context can be deliberately shared by separate projects, for example through a `.todo` symlink. Each primary checkout currently writes `worktrees.root`, so sibling projects overwrite one another's handoff state despite having independent project identities.

## What Changes

- **BREAKING** Namespace structured handoff entries by Guide project name before their worktree label: `projects.<project-name>.worktrees.<worktree-name>`.
- Keep `root` as the primary checkout's worktree label only; it is no longer the top-level identity for a handoff entry.
- Update handoff guidance, locking and merge instructions so an agent updates only its own project/worktree entry and preserves sibling projects plus global top-level data.
- Provide migration guidance for existing JSON and YAML handoff documents using the legacy `worktrees.<name>` layout.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `worktree-support`: namespace shared handoff state by project and worktree so separately configured projects can safely share a context file.

## Impact

- Handoff-context rendering and client-side merge instructions
- Worktree handoff, allocation, resume, and lock guidance
- Structured handoff documents that use the current `worktrees.<name>` layout
