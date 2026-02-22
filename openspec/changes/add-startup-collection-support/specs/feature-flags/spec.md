# feature-flags Specification Delta

## ADDED Requirements

### Requirement: Startup Instruction Flag
The system SHALL support a `startup-instruction` project flag for automatic content injection.

#### Scenario: Flag type and default
- **WHEN** accessing the `startup-instruction` flag
- **THEN** the flag type SHALL be string (optional)
- **AND** the default value SHALL be None (not set)
- **AND** empty string SHALL be treated as not set

#### Scenario: Flag validation
- **WHEN** setting the `startup-instruction` flag
- **THEN** the system SHALL validate the expression
- **AND** parse the expression to extract categories and collections
- **AND** verify all categories exist in the project
- **AND** verify all collections exist in the project
- **AND** patterns SHALL be ignored during validation

#### Scenario: Validation failure
- **WHEN** validation fails
- **THEN** reject the flag change
- **AND** return clear error message indicating which category/collection is invalid
- **AND** preserve the previous flag value

#### Scenario: Valid expression examples
- **WHEN** validating expressions
- **THEN** accept: `"guidelines"` (collection)
- **AND** accept: `"docs"` (category)
- **AND** accept: `"docs/README*"` (category with pattern)
- **AND** accept: `"guidelines+conventions"` (multiple collections)
- **AND** accept: `"docs/README*,guidelines"` (mixed)

#### Scenario: Flag retrieval
- **WHEN** retrieving the `startup-instruction` flag
- **THEN** return the raw expression string
- **AND** return None if not set
- **AND** return None if empty string
