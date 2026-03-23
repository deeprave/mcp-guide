# Models Specification

## MODIFIED Requirements

### Requirement: Category Model
The system SHALL provide a Category model with name, directory, patterns, and urls.

The `urls` field SHALL be an optional dict mapping pattern names (strings) to URL reference objects. Each URL reference object contains:
- `url` (required, string): The source URL
- `refresh` (optional, string): Refresh interval (default: "7d")

#### Scenario: Category validation with urls
- **WHEN** a Category is created with urls
- **THEN** name is validated (alphanumeric, hyphens, underscores)
- **AND** directory path is validated
- **AND** patterns list is validated (list of strings)
- **AND** urls dict is validated (pattern keys are strings, values contain valid URL)

#### Scenario: Category validation without urls
- **WHEN** a Category is created without urls
- **THEN** validation behaves as before
- **AND** urls defaults to empty dict
