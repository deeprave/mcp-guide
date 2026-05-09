## MODIFIED Requirements

### Requirement: Feature Flag Value Types
Feature flag values SHALL be restricted to supported types for consistency and validation.

The feature flag value model SHALL represent canonical boolean values as actual
booleans rather than boolean-looking strings.

The default feature flag contract SHALL support boolean and string values, while
structured values remain valid only for flags that explicitly opt into them
through registered validation and normalization.

#### Scenario: Boolean value remains typed
- **WHEN** a feature flag value is normalized to `true` or `false`
- **THEN** the feature flag value model SHALL store it as a boolean

#### Scenario: Arbitrary string remains typed as string
- **WHEN** a generic feature flag value is `"custom-mode"`
- **THEN** the feature flag value model SHALL store it as a string

#### Scenario: Structured value is preserved for registered flags
- **WHEN** a registered structured flag value is accepted by flag-specific
  validation
- **THEN** the feature flag value model SHALL preserve the structured value

### Requirement: Feature Flag Resolution
The system SHALL resolve feature flag values using project-specific → global → None hierarchy.

#### Scenario: Project flag takes precedence
- **WHEN** flag exists in both project and global configuration
- **THEN** return project-specific value

#### Scenario: Global flag fallback
- **WHEN** flag exists only in global configuration
- **THEN** return global value

#### Scenario: Flag not found
- **WHEN** flag does not exist in project or global configuration
- **THEN** return None

#### Scenario: Resolved boolean flag remains boolean
- **WHEN** a stored flag value has been normalized from `"true"` to boolean
  `true`
- **THEN** resolved flag access SHALL return the boolean value rather than the
  original string representation

