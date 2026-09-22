## Why

Git skills should integrate a project's delivery, issue-tracking, commit, and pull-request practices. They are workflow guidance, not thin wrappers around standard Git commands.

## What Changes

- Add `git-commit`, `git-push`, `git-pr`, and `git-sync` Guide skills.
- Add onboarding policies for issue tracking and delivery: `direct`, `branch`, and `multi-branch`.
- Let a change use, create, or deliberately omit an issue according to the selected tracker policy and the user's choice.
- Make `git-pr` compose commit, push, and repository pull-request practice.
- Make `git-sync` return a completed worktree to the current default branch.

## Impact

- Packaged skill templates, onboarding policy selection, and focused behaviour-level tests. The skills remain independently available without workflow or OpenSpec features.
