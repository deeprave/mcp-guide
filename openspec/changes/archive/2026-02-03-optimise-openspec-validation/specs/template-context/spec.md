## MODIFIED Requirements

### Requirement: OpenSpec Context Validation
The system SHALL perform OpenSpec validation once only and store the result with version permanently.

#### Scenario: One-time validation with version
- **WHEN** checking OpenSpec availability
- **THEN** verify file existence only (not read content)
- **AND** capture OpenSpec version
- **AND** store validation result as boolean flag
- **AND** store version string in context
- **AND** never re-validate while flag is true

### Requirement: Version-aware Template Context
The system SHALL provide OpenSpec version information in template context.

#### Scenario: Version available in templates
- **WHEN** rendering templates with OpenSpec context
- **THEN** include version string if available
- **AND** provide version comparison lambda
- **AND** support minimum version checks in templates

#### Scenario: Version comparison in templates
- **WHEN** template checks minimum version requirement
- **THEN** use lambda: `{{#openspec.has_version}}1.2.0{{/openspec.has_version}}`
- **AND** return true if current >= minimum
- **AND** return false if version missing or less than minimum
