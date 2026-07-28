## ADDED Requirements

### Requirement: Non-empty profile collections
The system SHALL reject a profile collection that does not declare at least one category or expression.

#### Scenario: Reject empty collection
- **WHEN** a profile containing a collection with an empty category list is loaded
- **THEN** profile validation SHALL fail with a descriptive error

#### Scenario: Apply complete default collection
- **WHEN** the default profile is applied to a new project
- **THEN** it SHALL include a code-review collection that resolves the review guidance
