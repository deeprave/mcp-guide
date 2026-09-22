## 1. Policies and skill packages

- [x] 1.1 Add issue-tracking and Git delivery policy families, including onboarding choices; verify selected policy partials are available through a controlled rendering fixture.
- [x] 1.2 Add flat `git-commit`, `git-push`, `git-pr`, and `git-sync` skill packages with required frontmatter; verify generic discovery without asserting the shipped inventory.

## 2. Policy-aware workflow guidance

- [x] 2.1 Implement `git-commit` guidance for tracker choice, issue creation/linking through available integrations, optional issue omission, delivery modes, branch naming, and commit policy.
- [x] 2.2 Implement `git-push` guidance that separates current-change work from unrelated pre-existing edits and uses `git-commit` before pushing approved work.
- [x] 2.3 Implement `git-pr` as the commit/push/PR-policy composition, including repository template handling and non-PR delivery modes.
- [x] 2.4 Implement `git-sync` for clean default-branch fast-forward and dirty-worktree user decisions, without branch deletion.

## 3. Verification and handover

- [x] 3.1 Add focused behavioural tests for policy-dependent delivery and skill rendering; do not assert literal shipped template prose.
- [x] 3.2 Document the Git policy and skill interactions for template authors and users.
- [x] 3.3 Run focused pytest coverage, Ruff check and format, strict OpenSpec validation, and `git diff --check`; full pytest passed (1,913 tests).

## 4. Review remediation

- [x] 4.1 Render selected policy partials on the public Git-skill resource path and replace helper-only coverage with selected-versus-unselected fixture behaviour.
- [x] 4.2 Align Git-skill and Git-policy metadata, headings, and operational guardrails with established conventions.
- [x] 4.3 Use available issue-tracker integrations for chosen creation or linking, and ask the user how to proceed when none is available.
- [x] 4.4 Document the policy-partial delivery convention and record deferred policy-conflict and provider-capability follow-ups.
- [x] 4.5 Run focused and complete validation for review remediation.
