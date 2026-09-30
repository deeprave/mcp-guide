# workflow-commands Specification

## Purpose

Define how the current-repository workflow commands choose a review target, a phase, and whether a
reset may change the workflow file.

## Requirements

### Requirement: Repository review target

The `workflow/review` command SHALL review one target in the current repository. When no target is
supplied, it SHALL request one of these choices: uncommitted work compared with `HEAD`, the current
branch compared with the repository default branch, a named branch compared with the default branch,
or a pull request in the current repository. A named branch SHALL require the branch name before
review starts. A pull request SHALL require its number in the current repository before review
starts. Supplied target values SHALL skip the corresponding request. The rendered command SHALL
name the selected comparison and SHALL still move the workflow into review.

#### Scenario: Uncommitted work is selected

- **WHEN** the review target is uncommitted work
- **THEN** the command instructs a review of the complete working tree against `HEAD`
- **AND** it does not ask for a branch name or pull-request number

#### Scenario: Current branch is selected

- **WHEN** the review target is the current branch
- **THEN** the command instructs a review of the current branch against the repository default branch
- **AND** it does not ask for another branch name

#### Scenario: Named branch needs a name

- **WHEN** the review target is a named branch and no branch name is supplied
- **THEN** the command requests the branch name before review starts

#### Scenario: Named branch is supplied

- **WHEN** the review target is a named branch and the branch name is supplied
- **THEN** the command instructs a review of that branch against the repository default branch

#### Scenario: Pull request number is supplied

- **WHEN** the review target is a pull request and its number is supplied
- **THEN** the command instructs a review of that pull request in the current repository

#### Scenario: Supplied target skips the request

- **WHEN** the invocation already supplies the review target values
- **THEN** the command renders the selected comparison without requesting those values again

#### Scenario: Missing review target renders guidance

- **WHEN** review target elicitation is unavailable or cancelled without a target
- **THEN** the command SHALL render guidance to choose one supported target
- **AND** it SHALL NOT fail because conditional follow-up forms have no target mode

#### Scenario: Unsupported review target renders guidance

- **WHEN** a rendered review target is not one of the supported modes
- **THEN** the command SHALL request a supported target before review begins

### Requirement: Enabled workflow phase choice

The `workflow/phase` command SHALL request a phase only when the invocation does not already name
one. The choices SHALL be the phases enabled by the current workflow project flag, excluding the
active phase. When no other enabled phase remains, the command SHALL NOT request a phase. A supplied
phase that is enabled SHALL be the phase written to the workflow file. A supplied phase that is not
enabled SHALL be rejected and SHALL NOT be written. A supplied phase that is already active SHALL
leave the workflow file unchanged.

#### Scenario: Missing phase offers enabled phases

- **WHEN** no phase is supplied and the workflow flag enables phases other than the active phase
- **THEN** the command requests one of those other enabled phases
- **AND** the active phase is not one of the choices

#### Scenario: Only the active phase is enabled

- **WHEN** no phase is supplied and the active phase is the only enabled phase
- **THEN** the command does not request a phase

#### Scenario: Missing phase renders choices

- **WHEN** phase elicitation is unavailable or cancelled without a phase
- **THEN** the command SHALL render the enabled phases other than the active phase
- **AND** it SHALL instruct the agent to obtain a selection before changing the workflow file

#### Scenario: Supplied phase is enabled

- **WHEN** the invocation names an enabled phase that is not the active phase
- **THEN** the command instructs the workflow file to be updated to that phase

#### Scenario: Supplied phase is unavailable

- **WHEN** the invocation names a phase that the workflow flag does not enable
- **THEN** the command rejects that phase
- **AND** it does not instruct the workflow file to be updated

#### Scenario: Supplied phase is already active

- **WHEN** the invocation names the active phase
- **THEN** the command leaves the workflow file unchanged

### Requirement: Workflow reset git guard

The `workflow/reset` command SHALL require the calling agent to inspect its own repository before
changing the workflow file. It SHALL leave the workflow file unchanged when the current branch is the
repository default branch. When the worktree has uncommitted changes and the current branch is not
the default branch, the command SHALL ask whether to stash those changes, apply the workflow reset,
and then restore the stash. Completion checks SHALL run before stashing. Declining SHALL leave the
workflow file unchanged. A clean worktree on a non-default branch SHALL continue the workflow-file
reset without a stash. The server SHALL NOT inspect or run Git commands against the calling agent's
repository.

#### Scenario: Default branch does nothing

- **WHEN** the current branch is the repository default branch
- **THEN** the command leaves the workflow file unchanged
- **AND** it does not ask to stash uncommitted changes

#### Scenario: Dirty feature branch accepts a stash

- **WHEN** the current branch is not the default branch and the worktree has uncommitted changes
- **AND** the user accepts the stash
- **THEN** the command instructs the changes to be stashed, the workflow reset to be applied, and
  the stash to be restored

#### Scenario: Dirty feature branch declines a stash

- **WHEN** the current branch is not the default branch and the worktree has uncommitted changes
- **AND** the user declines the stash
- **THEN** the command leaves the workflow file unchanged

#### Scenario: Clean feature branch resets

- **WHEN** the current branch is not the default branch and the worktree is clean
- **THEN** the command applies the workflow-file reset without stashing

#### Scenario: Calling agent performs repository checks

- **WHEN** the reset command is rendered
- **THEN** it SHALL require the calling agent to determine the default branch and worktree state in
  its own checkout
- **AND** the server SHALL NOT inspect the repository

#### Scenario: Explicit issue reset uses the same guards

- **WHEN** reset is invoked with an explicit issue identifier
- **THEN** the calling agent SHALL apply the same default-branch, completion, and stash guards before
  changing the workflow file
