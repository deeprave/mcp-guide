# Spec Delta

## ADDED Requirements

### Requirement: Production file content

The test suite SHALL NOT assert the literal source or rendered wording of a production template, document, or other production file. A test SHALL verify observable behaviour with fixtures or results that are not copies of production file text.

#### Scenario: Production template wording is asserted

- **WHEN** a test reads a production template, document, or other production file and asserts a phrase from that file
- **THEN** that test SHALL be removed from the suite

#### Scenario: Behaviour is verified without production wording

- **WHEN** a test verifies command or template behaviour through a fixture or a return value that is not production file text
- **THEN** the test SHALL be retained

#### Scenario: Workflow command fixtures

- **WHEN** workflow command elicitation or rendering behaviour needs coverage
- **THEN** the test SHALL use an isolated fixture entrypoint or resolver result
- **AND** it SHALL NOT read or assert production command template content
