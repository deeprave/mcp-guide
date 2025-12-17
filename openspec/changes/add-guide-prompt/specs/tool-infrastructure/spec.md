## ADDED Requirements

### Requirement: Direct Tool Invocation
The system SHALL allow prompts to call existing tools directly without decorator overhead.

#### Scenario: Tool function extraction
- **WHEN** prompt needs to call existing tool logic
- **THEN** tool implementation is accessible without decorator
- **AND** maintains same argument and context patterns