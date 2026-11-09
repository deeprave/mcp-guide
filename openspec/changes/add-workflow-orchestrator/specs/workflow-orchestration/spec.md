# Spec Delta

## Purpose

Define root-bound automated delivery coordination that turns aligned workflow
state into review-ready work without taking review judgement from the user.

## ADDED Requirements

### Requirement: Root-bound orchestration

Guide SHALL expose workflow orchestration only to a session bound to the root
worktree. It SHALL coordinate delivery after discussion or planning alignment
and SHALL not treat a linked-worktree agent as an orchestrator.

#### Scenario: Root session starts delivery
- **GIVEN** a root-bound session has aligned workflow state
- **WHEN** the agent starts orchestration
- **THEN** Guide SHALL provide delivery coordination guidance

#### Scenario: Linked worktree cannot orchestrate
- **GIVEN** a session is bound to a linked worktree
- **WHEN** the agent requests workflow orchestration
- **THEN** Guide SHALL withhold root orchestration guidance

### Requirement: Delegated worktree handoff

Guide SHALL let root orchestration delegate aligned work through the worktree
procedure. The handoff SHALL identify the issue, phase, plan when present,
worktree name, worktree path, branch, and child instructions.

#### Scenario: Orchestrator delegates an aligned issue
- **GIVEN** root workflow state identifies an issue and implementation plan
- **WHEN** orchestration delegates the issue
- **THEN** Guide SHALL prepare a handoff for a fresh linked-worktree agent
- **AND** SHALL preserve the issue and plan in that handoff

#### Scenario: Orchestrator lacks an issue
- **GIVEN** root workflow state has no selected issue
- **WHEN** orchestration attempts delegation
- **THEN** Guide SHALL require issue selection before preparing a handoff

### Requirement: Client-owned delivery actions

Guide SHALL provide the protocol for creating a linked worktree, updating the
handoff document, and starting a child agent, but SHALL NOT perform those
client-owned or platform-specific actions itself.

#### Scenario: Delegation protocol is rendered
- **WHEN** root orchestration prepares a delegated handoff
- **THEN** Guide SHALL instruct the root agent to perform the Git, handoff, and child-spawn actions
- **AND** SHALL not claim that Guide created the worktree or child agent

### Requirement: Constrained self-review correction

The orchestrator SHALL correct a self-review finding only when evidence shows a
failed validation, direct specification mismatch, clear scope creep, or
unnecessary complexity whose remedy requires no architectural or implementation
decision.

#### Scenario: Self-review finds a failed validation
- **GIVEN** self-review observes a failed validation caused by the implementation
- **WHEN** the correction is determined without a new design decision
- **THEN** the orchestrator SHALL correct the defect and repeat self-review

#### Scenario: Self-review finds unnecessary complexity
- **GIVEN** self-review observes complexity that exceeds the agreed work
- **WHEN** removing it requires no architectural or implementation decision
- **THEN** the orchestrator SHALL simplify the implementation and repeat self-review

### Requirement: Decision-required review findings

The orchestrator SHALL not resolve a finding that requires an architectural or
implementation decision. It SHALL record that finding in the worktree handoff
completion and include it in the review-ready handback for user-led triage.

#### Scenario: Self-review finds an architectural concern
- **GIVEN** self-review identifies an architectural concern
- **WHEN** resolving it requires an architectural or implementation decision
- **THEN** the orchestrator SHALL leave the implementation unchanged
- **AND** SHALL record the concern in the worktree handoff completion

#### Scenario: Independent review produces findings
- **GIVEN** an independent reviewer returns a finding
- **WHEN** root orchestration collates review results
- **THEN** it SHALL include the finding as triage input
- **AND** SHALL not apply a disposition or change because of it

### Requirement: Review-ready handback

After delivery work, the orchestrator SHALL hand control to the main root agent
with the implementation worktree, validation evidence, and concise triage
notes. The handback SHALL identify that worktree as the review target.

#### Scenario: Delegated implementation is ready for review
- **GIVEN** a linked-worktree agent finishes assigned delivery work
- **WHEN** orchestration completes its evidence and self-review collection
- **THEN** Guide SHALL provide the main agent with a review-ready handback
- **AND** SHALL identify the linked worktree for the subsequent review
