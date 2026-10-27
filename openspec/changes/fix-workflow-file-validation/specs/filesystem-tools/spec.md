# Spec Delta

## MODIFIED Requirements

### Requirement: Tool Results
The system SHALL return structured results using Result[T] pattern. A task failure produced while handling submitted filesystem content SHALL be preserved as a failure result and SHALL not be replaced with a generic successful receipt.

#### Scenario: Success result with data
- **WHEN** tool operation succeeds
- **THEN** returns Result.ok(data)
- **AND** success field is True
- **AND** includes operation statistics (cache hits, file count, etc.)
- **AND** includes optional message for agent guidance

#### Scenario: Failure result with error
- **WHEN** tool operation fails
- **THEN** returns Result.failure(error, error_type)
- **AND** success field is False
- **AND** error field contains clear error message
- **AND** error_type indicates failure category (security, validation, system)
- **AND** includes instruction for agent on how to proceed

#### Scenario: Submitted content triggers task validation failure
- **WHEN** a file-content submission triggers a task validation failure
- **THEN** the file-content tool SHALL return that failure to the agent
- **AND** it SHALL preserve the validation message
- **AND** it SHALL NOT return a generic successful receipt for the file

#### Scenario: Partial success with warnings
- **WHEN** tool operation completes with warnings
- **THEN** returns Result.ok(data)
- **AND** includes warnings field with list of issues
- **AND** message indicates partial success
- **AND** agent can decide whether to retry or accept result
