# Spec Delta

## MODIFIED Requirements

### Requirement: Workflow Content Processing
The workflow monitoring task SHALL process workflow file content by comparing valid state against cached previous state and generating semantic change responses. When parsing succeeds and no semantic workflow-change response is available, the task SHALL render the workflow state-format template and use a non-`None` render as the file-content response, preserving its content, instruction, and disposition. The task SHALL update cached state only after processing valid changes. Invalid submitted content SHALL return a clear failure and SHALL not replace cached state or be acknowledged as a successful workflow-file receipt.

#### Scenario: Content processing workflow
- **WHEN** valid workflow file content is received
- **THEN** system SHALL parse the new content into workflow state
- **AND** system SHALL compare against cached previous state (if available)
- **AND** system SHALL generate appropriate change events based on differences
- **AND** system SHALL queue contextual instructions based on change types
- **AND** system SHALL update cached state only after processing changes

#### Scenario: Parsed workflow content without semantic changes
- **WHEN** workflow file content parses successfully
- **AND** no semantic workflow-change response is generated
- **THEN** system SHALL render the workflow state-format template
- **AND** a non-`None` render SHALL replace the file-content response with its content, instruction, and disposition

#### Scenario: Workflow state-format template is unavailable
- **WHEN** workflow file content parses successfully
- **AND** no semantic workflow-change response is generated
- **AND** rendering the workflow state-format template returns `None`
- **THEN** system SHALL retain the normal file-content response

#### Scenario: Semantic workflow change response takes precedence
- **WHEN** workflow file content produces a semantic workflow-change response
- **THEN** system SHALL return the semantic workflow-change response
- **AND** system SHALL NOT replace it with workflow state-format guidance

#### Scenario: Invalid workflow-file submission
- **WHEN** submitted workflow file content is invalid YAML, is not a mapping, omits `phase`, or has a field with an invalid schema type
- **THEN** the file-content operation SHALL return a failure identifying the invalid workflow file
- **AND** the system SHALL NOT cache submitted state
- **AND** the system SHALL NOT acknowledge the submission as successfully received

#### Scenario: Error handling during comparison
- **WHEN** workflow content parsing or comparison fails
- **THEN** system SHALL log appropriate warnings
- **AND** system SHALL not update cached state
- **AND** system SHALL not queue potentially incorrect change instructions
