## 1. Bundled Git skill packages

- [ ] 1.1 Add flat `git-commit`, `git-push`, `git-pr`, and `git-worktree-reset` SKILL.md package templates with required skill frontmatter; verify the existing skill catalogue discovers each through a controlled package-layout test.
- [ ] 1.2 Write `git-commit` guidance that protects `main`, creates a `<commit-type>/[<issue-id>-]<slug>` branch when needed, and uses a concise issue-aware commit message; manually review it against the Git-skills specification.
- [ ] 1.3 Write `git-push` guidance that requires a branch and establishes its matching upstream when required; manually review it against the Git-skills specification.
- [ ] 1.4 Write `git-pr` guidance that composes the commit and push practices, avoids duplicate pull requests, and uses the repository pull-request format; manually review it against the Git-skills specification.
- [ ] 1.5 Write `git-worktree-reset` guidance that stops for uncommitted or unpushed work, then switches to main, runs `git fetch -atpf`, fast-forwards safely, and conditionally returns to workflow discussion; manually review it against the Git-skills specification.

## 2. Conditional context and verification

- [ ] 2.1 Apply workflow and OpenSpec conditionals only to instructions that refer to those optional features; verify a controlled rendering fixture keeps every Git skill available without either flag.
- [ ] 2.2 Add focused behaviour tests for generic skill discovery and feature-conditional rendering without asserting production template text or package inventory; run the relevant pytest selection.
- [ ] 2.3 Run Ruff check and format, strict OpenSpec validation, and `git diff --check`; record any full-suite result or environmental blocker.
