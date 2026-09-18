## Purpose

Provide bundled Git skills that guide agents through safe, consistent delivery
and cleanup practice without coupling ordinary Git work to optional workflows.

## ADDED Requirements

### Requirement: Git skills are independently available
The system SHALL provide `git-commit`, `git-push`, `git-pr`, and
`git-worktree-reset` as bundled Guide skill packages. Their discovery and
rendering SHALL NOT require workflow or OpenSpec features to be enabled.
Instructions that refer to an enabled workflow, workflow file, or OpenSpec
change SHALL be conditional on the corresponding feature.

#### Scenario: Project has no workflow configuration
- **WHEN** an agent retrieves a bundled Git skill for a project without an
  enabled workflow or OpenSpec feature
- **THEN** the skill SHALL remain available
- **AND** it SHALL NOT require a workflow or OpenSpec action to perform its
  Git hygiene guidance

### Requirement: Commit skill protects the main branch
The `git-commit` skill SHALL direct an agent not to commit project changes to
`main`. When the current branch is `main`, it SHALL direct the agent to create
and select a branch named `<commit-type>/[<issue-id>-]<slug>` before committing.
The commit type SHALL be a suitable conventional category, including
`feature`, `chore`, `bugfix`, or `release`; the optional issue identifier SHALL
be included when an applicable identifier is already available.

#### Scenario: Commit begins from main
- **WHEN** an agent uses `git-commit` while the project checkout is on `main`
- **THEN** it SHALL create and select an appropriately named branch before
  creating a commit
- **AND** it SHALL NOT create the commit directly on `main`

#### Scenario: Applicable issue identifier exists
- **WHEN** an agent uses `git-commit` and the current work has an applicable
  issue identifier
- **THEN** the branch and concise commit message SHALL include that identifier
- **AND** the agent SHALL NOT invent an identifier or create a new issue unless
  the user has requested that action

### Requirement: Push skill publishes only branch work
The `git-push` skill SHALL direct an agent to push from a branch, not `main`.
It SHALL establish an upstream branch matching the local branch when one is
required for the push.

#### Scenario: Branch has no upstream
- **WHEN** an agent uses `git-push` from an eligible branch without an upstream
- **THEN** it SHALL push the branch and establish its matching upstream

### Requirement: Pull-request skill composes delivery steps
The `git-pr` skill SHALL direct an agent through the `git-commit` and
`git-push` practices before pull-request creation when the project uses a
branch-and-pull-request delivery model. It SHALL create a pull request only
when the current branch has no existing pull request and SHALL use the
repository's agreed pull-request format.

#### Scenario: Project does not use pull requests
- **WHEN** an agent uses `git-pr` for a project that does not use a
  branch-and-pull-request delivery model
- **THEN** the skill SHALL NOT require pull-request creation
- **AND** it SHALL still apply the relevant commit and push hygiene

#### Scenario: Pull request already exists
- **WHEN** an agent uses `git-pr` for a branch that already has a pull request
- **THEN** it SHALL NOT create a duplicate pull request
- **AND** it SHALL report or use the existing pull request as appropriate

### Requirement: Worktree reset preserves outstanding work
The `git-worktree-reset` skill SHALL verify that the worktree has no
uncommitted changes and no commits awaiting push before changing branches. If
either condition is not met, it SHALL ask the user for direction rather than
discarding, resetting, or hiding work. Once clean, it SHALL switch to `main`,
fetch all remotes, tags, and pruning updates, and fast-forward local `main` to
its configured upstream. If workflow support is enabled, it SHALL then direct
the agent to the workflow discussion phase.

#### Scenario: Reset finds outstanding work
- **WHEN** an agent uses `git-worktree-reset` and finds uncommitted or unpushed
  work
- **THEN** it SHALL ask the user for direction
- **AND** it SHALL NOT discard, reset, stash, or otherwise hide that work

#### Scenario: Reset begins clean
- **WHEN** an agent uses `git-worktree-reset` and the worktree is clean with no
  commits awaiting push
- **THEN** it SHALL switch to `main`, fetch remotes, tags, and pruning updates,
  and fast-forward to the configured upstream main branch
