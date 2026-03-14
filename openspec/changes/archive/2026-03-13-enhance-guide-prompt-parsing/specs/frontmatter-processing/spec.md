## ADDED Requirements

### Requirement: Argument Requirements Field
Frontmatter SHALL support `argrequired` top-level field to declare command flags that require values.

#### Scenario: Frontmatter with argrequired
- **WHEN** template frontmatter contains:
  ```yaml
  argrequired:
    - tracking
    - issue
  ```
- **THEN** system SHALL parse `argrequired` as list of strings
- **AND** pass this list to command parser for argument processing

#### Scenario: Frontmatter without argrequired field
- **WHEN** template frontmatter does not contain `argrequired` field
- **THEN** system SHALL treat `argrequired` as empty list
- **AND** all flags use default boolean behavior

#### Scenario: Invalid argrequired format
- **WHEN** `argrequired` is not a list (e.g., string or dict)
- **THEN** system SHALL log warning about invalid format
- **AND** treat `argrequired` as empty list
- **AND** continue processing with default behavior
