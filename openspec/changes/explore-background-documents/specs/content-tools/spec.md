## ADDED Requirements

### Requirement: Background Document Import

The server SHALL provide a command template that generates delegation-ready task descriptions for background document imports, if the exploration proves viable.

The template SHALL accept file paths, category, and metadata parameters and render a structured task description suitable for agent-side delegation.

#### Scenario: Generate import delegation task
- **WHEN** agent executes `document/import` with a list of file paths and target category
- **THEN** command returns a natural language task description suitable for delegation to a background agent

#### Scenario: Background agent executes import
- **WHEN** a background agent receives the delegation task description
- **THEN** it reads each file and calls `send_file_content` with the specified category and metadata
