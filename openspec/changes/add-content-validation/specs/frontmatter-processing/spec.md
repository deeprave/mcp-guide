## ADDED Requirements

### Requirement: Frontmatter Schema Validation
The system SHALL provide a frontmatter schema validator that checks documents for unknown keys, type mismatches, and invalid flag references at authoring time.

#### Scenario: Unknown frontmatter key
- **WHEN** a document contains a frontmatter key not in the known schema
- **THEN** the validator SHALL report it as a warning with the document path and key name

#### Scenario: Type mismatch on known key
- **WHEN** a known frontmatter key contains a value of the wrong type (e.g. `requires-workflow: "yes"` instead of boolean)
- **THEN** the validator SHALL report it as an error with the expected type

#### Scenario: Valid frontmatter passes
- **WHEN** all frontmatter keys are known and their values match the expected types
- **THEN** the validator SHALL report no issues for that document

### Requirement: Requires-Flag Reference Validation
The system SHALL validate that `requires-<flag>` frontmatter keys reference defined feature flags.

#### Scenario: Unknown flag in requires directive
- **WHEN** a document contains `requires-unknown-flag: true`
- **THEN** the validator SHALL report a warning that `unknown-flag` is not a recognised feature flag

#### Scenario: Known flag in requires directive
- **WHEN** a document contains `requires-workflow: true`
- **THEN** the validator SHALL accept the directive without issue

### Requirement: Docs Validate Command
The system SHALL provide a `:docs/validate` prompt command that runs all content validators across the current project and reports results.

#### Scenario: Validation report with issues
- **WHEN** `:docs/validate` is invoked and issues are found
- **THEN** the system SHALL display issues grouped by document path with severity (error/warning) and description

#### Scenario: Clean project passes validation
- **WHEN** `:docs/validate` is invoked and no issues are found
- **THEN** the system SHALL report that all documents passed validation

#### Scenario: Strict mode promotes warnings to errors
- **WHEN** `:docs/validate --strict` is invoked
- **THEN** warnings SHALL be treated as errors in the exit status

#### Scenario: CLI validate flag for CI use
- **WHEN** the server is invoked with `--validate`
- **THEN** the system SHALL run validation, print the report, and exit with a non-zero status if any errors were found
