# Spec Delta

## Purpose

Provide rapid, dependency-aware local test feedback while preserving comprehensive
pytest validation for pull requests and usable evidence about suite duration.

## ADDED Requirements

### Requirement: Affected local test selection
The development workflow SHALL select tests affected by staged implementation or
test changes for the local commit feedback loop. Selection SHALL include directly
changed tests and tests whose exercised or declared dependency path reaches changed
project code. When the selector cannot establish a safe scope, it SHALL expand to
the applicable test suite rather than omit potentially affected tests.

#### Scenario: Changed implementation module
- **WHEN** a staged project module changes
- **THEN** the local feedback run executes tests selected through its dependency path
- **AND** it does not require the complete pytest inventory when the scope is known

#### Scenario: Changed test module
- **WHEN** a staged test module changes
- **THEN** the local feedback run executes that changed test module

#### Scenario: Broad-impact input
- **WHEN** a staged change affects dependency configuration, pytest configuration,
  test plugins, shared fixtures, or another configured broad-impact input
- **THEN** the local feedback run expands to the applicable test suite

### Requirement: Complete pull-request validation
The pull-request workflow SHALL run the complete pytest inventory independently of
local affected-test selection. A successful affected local run SHALL NOT replace or
weaken the complete pull-request validation requirement.

#### Scenario: Pull request after an affected local run
- **WHEN** a pull request is created after local affected-test selection succeeds
- **THEN** the pull-request workflow still runs the complete pytest inventory

### Requirement: Test execution classification
The test suite SHALL provide pytest marks for unit, integration, synchronisation,
timing-dependent, and slow test classes. Tests under the established unit and
integration hierarchy SHALL receive their corresponding marks by location where
that classification is unambiguous.

#### Scenario: Hierarchy-classified test
- **WHEN** a test is collected from an established unit or integration test path
- **THEN** it receives the corresponding pytest mark

#### Scenario: Timing-dependent test
- **WHEN** a test relies on scheduling, elapsed time, or concurrent synchronisation
- **THEN** it carries the timing-dependent or synchronisation mark as applicable

### Requirement: Test-duration evidence
The continuous-integration workflow SHALL emit JUnit XML for designated pytest
executions and retain accumulated duration evidence by test class. Duration evidence
SHALL support identifying slow or unstable feedback paths without changing the
complete pull-request validation requirement.

#### Scenario: Designated pytest workflow executes
- **WHEN** the designated test workflow runs
- **THEN** it produces JUnit XML containing per-test duration information

#### Scenario: Duration data is accumulated
- **WHEN** duration records from multiple workflow runs are available
- **THEN** the accumulated evidence distinguishes the registered test classes

### Requirement: Reversible selection trial
Affected-test selection SHALL be introduced as an experiment with an explicit
fallback to existing complete local execution. Disabling or reverting the trial
SHALL leave the pull-request pytest workflow and test classification data usable.

#### Scenario: Trial is disabled
- **WHEN** the affected-test experiment is disabled or reverted
- **THEN** local commits use the existing complete pytest execution path
- **AND** pull-request validation remains unchanged
