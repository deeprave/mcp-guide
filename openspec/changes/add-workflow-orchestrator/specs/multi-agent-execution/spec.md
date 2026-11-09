# Spec Delta

## Purpose

Define portable delegated-agent execution over shared worktrees without making
the workflow depend on a particular agent harness or child-spawn mechanism.

## ADDED Requirements

### Requirement: Eligible multi-agent runner

Guide SHALL treat an agent runner as eligible for delegated work only when it
is separately authorised, can access the assigned worktree, and has Guide MCP
available. Guide SHALL not infer eligibility from the parent agent session.

#### Scenario: Eligible runner receives a handoff
- **GIVEN** a runner is authorised, can access the assigned worktree, and has Guide MCP
- **WHEN** root orchestration delegates work
- **THEN** Guide SHALL provide that runner's child bootstrap instructions

#### Scenario: Parent access does not establish child eligibility
- **GIVEN** the root agent has Guide MCP and worktree access
- **WHEN** a different agent runner lacks either capability
- **THEN** Guide SHALL not treat that runner as eligible

### Requirement: Fresh delegated Guide session

An eligible delegated runner SHALL establish a fresh Guide session bound to the
shared project root and assigned worktree. It SHALL read the durable handoff
and local workflow state without receiving the parent Guide session identifier.

#### Scenario: Runner begins delegated work
- **GIVEN** a runner receives an assigned worktree handoff
- **WHEN** it starts the delegated task
- **THEN** it SHALL bind a fresh Guide session to the assigned worktree
- **AND** SHALL use the handoff and local workflow file as its task context

### Requirement: Manual runner fallback

When no eligible runner is available, Guide SHALL preserve the delegated
handoff and provide the root agent with instructions for manually starting a
compatible child session in the assigned worktree.

#### Scenario: No runner is available
- **GIVEN** root orchestration has prepared a delegated handoff
- **WHEN** no eligible runner is available
- **THEN** Guide SHALL retain the handoff unchanged
- **AND** SHALL render manual child-session bootstrap instructions

### Requirement: Runner-neutral completion reporting

A delegated runner SHALL report work through the assigned worktree workflow
file and review artefacts. The root agent SHALL use those records for later
review and triage regardless of the runner that performed the work.

#### Scenario: Different runners complete equivalent handoffs
- **GIVEN** two eligible runners complete delegated work in separate worktrees
- **WHEN** each updates its workflow and review records
- **THEN** root orchestration SHALL present both worktrees as review targets
- **AND** SHALL not require runner-specific result formats

### Requirement: Generic multi-agent invocation

Root orchestration SHALL allow a selected set of eligible runners to invoke a
permitted Guide command or skill. Each invocation SHALL receive an isolated
handoff and fresh Guide session for its assigned worktree.

#### Scenario: Orchestrator fans out a Guide skill
- **GIVEN** root orchestration selects eligible runners and a permitted Guide skill
- **WHEN** it prepares multi-agent execution
- **THEN** Guide SHALL prepare one runner handoff for each selection
- **AND** each handoff SHALL identify the same requested Guide skill

#### Scenario: Orchestrator fans out a Guide command
- **GIVEN** root orchestration selects eligible runners and a permitted Guide command
- **WHEN** it prepares multi-agent execution
- **THEN** Guide SHALL prepare one runner handoff for each selection
- **AND** each handoff SHALL identify the same requested Guide command

### Requirement: Independent multi-agent review

Root orchestration SHALL support multi-agent review by assigning selected
eligible runners the same implementation worktree and `workflow-review`. Each
runner SHALL produce an independently attributable review result for root-led
user triage.

#### Scenario: Four runners review one implementation
- **GIVEN** root orchestration selects four eligible runners for review
- **WHEN** it fans out `workflow-review` for an implementation worktree
- **THEN** each runner SHALL receive an isolated review handoff for that worktree
- **AND** root orchestration SHALL collect four attributable review results
