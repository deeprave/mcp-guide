## ADDED Requirements

### Requirement: Policy Conflict Rule Registry
The system SHALL maintain a conflict rule registry that identifies known contradictory or redundant combinations of active policy selections.

#### Scenario: Conflict rule structure
- **WHEN** the conflict registry is loaded
- **THEN** each rule SHALL specify: the set of policy paths that trigger the conflict, a human-readable explanation, and a severity level (warning or info)

#### Scenario: Rule registry is data-driven
- **WHEN** conflict rules are evaluated
- **THEN** the rules SHALL be loaded from a data file or template rather than hardcoded in application code
- **AND** adding a new rule SHALL not require changes to application logic

### Requirement: Conflict Detection on Policy Selection
When a policy is selected, the system SHALL check the resulting active policy set against the conflict registry and surface any matches.

#### Scenario: Conflict detected on selection
- **WHEN** a user selects a policy that creates a known conflict with an already-active policy
- **THEN** the system SHALL apply the selection
- **AND** SHALL surface a warning identifying the conflicting policies and the nature of the contradiction

#### Scenario: No conflict on selection
- **WHEN** a user selects a policy that creates no known conflict
- **THEN** the selection SHALL complete without any conflict warning

#### Scenario: Conflict is a warning, not a block
- **WHEN** a conflict is detected
- **THEN** the policy selection SHALL still be applied
- **AND** the system SHALL NOT prevent or roll back the selection

### Requirement: Policies Check Command
The system SHALL provide a `:policies/check` prompt command that validates the project's full active policy set against the conflict registry.

#### Scenario: Conflicts present in current configuration
- **WHEN** `:policies/check` is invoked and the active policy set contains known conflicts
- **THEN** the system SHALL list each conflict with the affected policy paths and a plain-language explanation

#### Scenario: No conflicts in current configuration
- **WHEN** `:policies/check` is invoked and no conflicts are detected
- **THEN** the system SHALL confirm that no conflicts were found in the active policy set

#### Scenario: Suggested resolution included
- **WHEN** a conflict is reported by `:policies/check`
- **THEN** the output SHOULD include a suggested resolution or the trade-off the user should consider
