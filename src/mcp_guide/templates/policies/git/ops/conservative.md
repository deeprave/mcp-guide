---
type: agent/instruction
description: >
  Git Policy: Conservative (Read-Only). The agent may use read-only git operations but must not modify the working tree, index, or history.
---
# Git Policy: Conservative (Read-Only)

The agent may use read-only git operations but must not modify the working tree,
index, or history.

## Permitted

- `git status`, `git diff`, `git log`, `git show`
- `git branch --list`, `git tag --list`
- `git stash list` (read only)

## Forbidden

- `git add`, `git commit`, `git push`
- `git reset`, `git restore`, `git checkout`, `git switch`
- `git rebase`, `git merge`, `git stash push/pop`
- Any operation that modifies the index, working tree, or history

## Rationale

Useful when the agent needs to inspect repository state (e.g. check what has
changed before reviewing), but the user still owns all write operations.
