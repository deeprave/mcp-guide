# git-skills Specification

## Purpose
Provide policy-aware Git workflow skills without reducing them to command wrappers.

## Requirements

### Requirement: Git skills are independently available
The system SHALL provide `git-commit`, `git-push`, `git-pr`, `git-sync`, and
`git-pr-triage` as bundled Guide skill packages. Their discovery and rendering
SHALL NOT require workflow or OpenSpec features. Instructions that refer to
optional features SHALL be conditional on those features.

#### Scenario: Features are disabled
- **WHEN** workflow and OpenSpec features are disabled
- **THEN** each Git skill remains available without feature-specific instructions

### Requirement: Onboarding selects Git delivery and issue policies
Onboarding SHALL select `issue-tracking/<provider>` and `git/delivery/<mode>` policies. Providers SHALL include `none`, Jira, Linear, Redmine, Asana, YouTrack, GitHub Issues, GitLab, Bugzilla, Mantis, Monday.com, Trello, Wrike, Shortcut, Trac, Basecamp, and Phabricator. Modes SHALL be `direct`, `branch`, and `multi-branch`.

#### Scenario: User configures Git policies
- **WHEN** onboarding configures Git workflow practice
- **THEN** it offers a tracker provider and a delivery mode

### Requirement: Commit skill applies issue and delivery policy
`git-commit` SHALL use the selected delivery and issue-tracking policies. For a non-`none` tracker with no issue, it SHALL ask whether to create or link an issue or proceed without one; when creation or linking is chosen, it SHALL use an available integration or ask the user how to proceed if none is available. A branch, where used, SHALL be named `<commit-type>/[<issue-id>-]<commit-slug>`. Commit formatting SHALL follow the selected commit policy.

#### Scenario: Tracked change has no issue
- **WHEN** `git-commit` runs under a non-`none` tracker policy without an issue
- **THEN** it asks the user to create, link, or omit an issue

### Requirement: Push skill protects unrelated work
`git-push` SHALL commit current-change work by default. When it detects other changed files that it did not create, it SHALL ask whether to include or omit them, using `git-commit` for approved inclusion, before pushing all selected work.

#### Scenario: Unrelated edits are present
- **WHEN** `git-push` detects edits outside the current change that the agent did not create
- **THEN** it asks whether to include or leave them untouched before pushing

### Requirement: Pull-request skill composes delivery work
`git-pr` SHALL compose `git-commit` and `git-push`. For `branch` delivery it SHALL create or reuse a pull request according to the selected PR policy and any repository template. For other delivery modes it SHALL not require a PR.

#### Scenario: Branch delivery requires a pull request
- **WHEN** `git-pr` is used with `branch` delivery
- **THEN** it applies commit and push guidance before creating or reusing a PR

### Requirement: Sync returns to the default branch safely
`git-sync` SHALL synchronise a completed worktree with its remote default branch. On the default branch it SHALL fetch and fast-forward. On another branch it SHALL switch to the default branch, fetch, and fast-forward. If the worktree is dirty, it SHALL treat that as an abnormal handover condition and ask the user whether to preserve the work while switching, handle it as existing branch work, or stop. It SHALL not delete branches.

#### Scenario: Sync finds deferred work
- **WHEN** `git-sync` finds uncommitted changes
- **THEN** it asks the user how to handle them and does not delete a branch

### Requirement: Git skill tests verify behaviour
Tests SHALL verify discovery, policy-dependent rendering, and delivered behaviour without asserting specific shipped template prose or inventories.

#### Scenario: A policy changes delivered guidance
- **WHEN** a controlled rendering fixture selects a Git policy
- **THEN** the test observes the resulting behaviour without asserting template prose
