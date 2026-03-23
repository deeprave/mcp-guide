# Category Tools Specification

## MODIFIED Requirements

### Requirement: Category Client Document Patterns
The Category model SHALL support a `client` dict mapping patterns to client-side document paths.

#### Scenario: Add category with client patterns
- **WHEN** category is created with `client={"*.md": "docs/*.md"}`
- **THEN** category stores client pattern mappings
- **AND** patterns support glob syntax in both key and value

### Requirement: Client Path Validation on Add
The system SHALL validate client paths against `allowed_read_paths` when adding to category.

#### Scenario: Add valid client path
- **WHEN** client path is within `allowed_read_paths`
- **THEN** path is added to category
- **AND** relative paths are resolved to client pwd

#### Scenario: Add invalid client path
- **WHEN** client path is outside `allowed_read_paths`
- **THEN** system warns user
- **AND** path is still added (validation enforced at request time)
