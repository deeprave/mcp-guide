---
type: agent/instruction
description: >
  Git Policy: No Git Operations (Default). The agent must never perform any git operations autonomously.
---
# Git Policy: No Git Operations (Default)

The agent must never perform any git operations autonomously.

## Rules

The following operations are **forbidden** without explicit user request:

- `git add`, `git stage`
- `git commit`
- `git push`, `git push --force`
- `git revert`, `git reset`, `git restore`
- `git checkout`, `git switch`
- `git rebase`, `git merge`
- `git filter-branch`, `git stash`

All of these operations are destructive to or irreversible in the working tree.
Fix errors manually or request user assistance.

## Rationale

Source control history is the team's record of intent. The user must sign every
commit. This policy is appropriate when auditability, commit authorship, and
review of staged changes are important.
