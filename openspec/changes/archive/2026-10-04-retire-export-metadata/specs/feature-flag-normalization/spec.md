# Spec Delta

## MODIFIED Requirements

### Requirement: Registered Flag Override Precedence

Feature flags that register a custom validator or normaliser SHALL continue to
use their registered behavior instead of the default boolean-or-string path.

#### Scenario: Registered path flag keeps custom normalization
- **WHEN** `path-documents` is set to `"docs"`
- **THEN** the registered path normaliser SHALL run
- **AND** the stored value SHALL reflect the path-specific normalization rather
  than the default scalar-only path

#### Scenario: Registered workflow flag keeps structured validation
- **WHEN** `workflow` is set to a valid phase list
- **THEN** the registered workflow validator SHALL accept the structured value
- **AND** the default boolean-or-string validator SHALL NOT reject it
