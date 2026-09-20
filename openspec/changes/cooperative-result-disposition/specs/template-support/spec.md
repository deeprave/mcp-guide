## MODIFIED Requirements

### Requirement: Template Error Handling

The system SHALL handle template errors gracefully with proper error reporting.

Error handling SHALL:
- Catch Chevron parsing and rendering errors
- Return Result.failure with error_type "template_error"
- Log template errors at WARNING level
- Provide clear error messages with file path and error details
- Set disposition `agent/error` so the taught vocabulary conveys that the failure is fixable by the agent, without a paired prose restatement
- Never fall back to raw template content

#### Scenario: Template parse error
- **WHEN** template has malformed mustache syntax
- **THEN** return Result.failure with specific parse error message

#### Scenario: Template render error
- **WHEN** template rendering fails during execution
- **THEN** return Result.failure with rendering error details

#### Scenario: Error logging
- **WHEN** template error occurs
- **THEN** log error at WARNING level with file path and error message

#### Scenario: Agent error instruction
- **WHEN** template error occurs
- **THEN** set disposition `agent/error` on the result
- **AND** do not additionally include a paired instruction restating what the disposition already conveys

#### Scenario: No fallback behavior
- **WHEN** template error occurs
- **THEN** do not return raw template content, always return error Result
