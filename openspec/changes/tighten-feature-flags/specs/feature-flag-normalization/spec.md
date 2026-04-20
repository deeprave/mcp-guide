## ADDED Requirements

### Requirement: Default Feature Flag Normalization

The system SHALL apply a default validator and normaliser for feature flags that
do not register a more specific validator and normaliser.

The default feature flag contract SHALL accept only:

- boolean values
- arbitrary string values

The default normaliser SHALL preserve arbitrary strings unchanged.

#### Scenario: Generic boolean flag remains boolean
- **WHEN** an unregistered feature flag is set to `true`
- **THEN** the stored feature flag value SHALL be the boolean `true`

#### Scenario: Generic arbitrary string flag is preserved
- **WHEN** an unregistered feature flag is set to `"custom-mode"`
- **THEN** the stored feature flag value SHALL remain the string `"custom-mode"`

#### Scenario: Unsupported generic structured value is rejected
- **WHEN** an unregistered feature flag is set to a list or dictionary value
- **THEN** the feature flag operation SHALL reject the value as invalid

### Requirement: Canonical Boolean Coercion

The default normaliser SHALL coerce canonical boolean-like string inputs to
actual boolean values.

#### Scenario: True string normalizes to boolean true
- **WHEN** an unregistered feature flag is set to the string `"true"`
- **THEN** the stored feature flag value SHALL be the boolean `true`

#### Scenario: False string normalizes to boolean false
- **WHEN** an unregistered feature flag is set to the string `"false"`
- **THEN** the stored feature flag value SHALL be the boolean `false`

#### Scenario: Non-boolean string is not coerced
- **WHEN** an unregistered feature flag is set to the string `"review"`
- **THEN** the stored feature flag value SHALL remain the string `"review"`

### Requirement: Registered Flag Override Precedence

Feature flags that register a custom validator or normaliser SHALL continue to
use their registered behavior instead of the default boolean-or-string path.

#### Scenario: Registered path flag keeps custom normalization
- **WHEN** `path-export` is set to `"docs"`
- **THEN** the registered path normaliser SHALL run
- **AND** the stored value SHALL reflect the path-specific normalization rather
  than the default scalar-only path

#### Scenario: Registered workflow flag keeps structured validation
- **WHEN** `workflow` is set to a valid phase list
- **THEN** the registered workflow validator SHALL accept the structured value
- **AND** the default boolean-or-string validator SHALL NOT reject it

