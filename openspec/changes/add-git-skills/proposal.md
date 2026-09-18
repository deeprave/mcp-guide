## Why

Agents can run Git commands successfully while still leaving worktree hygiene,
branch naming, commit messages, and pull-request handling inconsistent. Guide
needs explicit, reusable skills that establish those practices without making
ordinary Git actions depend on the project workflow or OpenSpec configuration.

## What Changes

- Add bundled `git-commit`, `git-push`, `git-pr`, and `git-worktree-reset`
  skills for Git hygiene and delivery workflows.
- Require project-specific Git skills to avoid committing or pushing directly
  to `main`, create a purpose-named branch when needed, and use concise,
  traceable commit messages.
- Define `git-pr` as the composed commit-and-push workflow that creates a
  pull request only when none exists for the branch.
- Define `git-worktree-reset` as a safe return to an up-to-date `main` after
  confirming there is no uncommitted or unpushed work.
- Keep these skills independently available regardless of workflow or
  OpenSpec flags. Any instructions that mention those features remain
  conditional on the corresponding feature being enabled.

## Capabilities

### New Capabilities

- `git-skills`: Bundled Guide skill packages that direct agents through safe,
  consistent branch, commit, push, pull-request, and worktree-reset practice.

### Modified Capabilities

None.

## Impact

- New packaged skill templates under `src/mcp_guide/templates/_skills/`.
- Guide skill discovery and resource delivery surface the new packages without
  requiring any workflow or OpenSpec flag.
- Focused behavioural tests cover discovery, rendering conditions, and the
  safety guidance exposed by the skills.
