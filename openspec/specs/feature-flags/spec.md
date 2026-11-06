# feature-flags Specification

## Purpose
Define feature-flag values, scope, resolution, and runtime behaviour.

## Requirements

### Requirement: Feature Flags Use A Dedicated Runtime Value Abstraction

The feature flag system SHALL use a dedicated runtime feature-value abstraction
instead of treating flag values purely as raw nested Python data throughout the
system.

#### Scenario: Construct feature value from supported raw shapes
- **GIVEN** a raw flag value represented as a supported scalar, list, or dict
- **WHEN** the system accepts or loads that flag value
- **THEN** it constructs a dedicated runtime feature-value object
- **AND** it rejects unsupported raw shapes

#### Scenario: Raw serialization remains compatible
- **GIVEN** a valid runtime feature-value object
- **WHEN** the system persists or exports that value
- **THEN** it serializes to the same externally supported raw flag shape
- **AND** existing user-facing configuration syntax remains valid

#### Scenario: Feature value provides display-safe rendering
- **GIVEN** a valid runtime feature-value object
- **WHEN** display-oriented code needs a user-facing representation
- **THEN** the feature-value abstraction provides a stable display form
- **AND** callers do not need to inspect raw nested structures directly

#### Scenario: Flag resolution preserves abstraction
- **GIVEN** project and global flags are available
- **WHEN** the system resolves the effective value for a flag
- **THEN** the resolved result is returned through the dedicated runtime
  feature-value abstraction
- **AND** callers do not need to reconstruct the abstraction manually

### Requirement: Global Feature Flags Are Process-Owned
Global feature-flag list, get, set, and remove operations SHALL be owned by the
process runtime, which SHALL persist them through the configuration service.
The global feature-flag handler SHALL NOT depend on a Session or on a direct
configuration-service reference.

Project feature flags remain part of the bound project's configuration and are
outside this requirement.

#### Scenario: Global flag is read or written
- **WHEN** an operation lists, gets, sets, or removes a global feature flag
- **THEN** it SHALL go through the process runtime
- **AND** the runtime SHALL persist the change in the shared configuration
- **AND** the handler SHALL NOT require a Session or a configuration-service
  object

#### Scenario: Project flag is unchanged in ownership
- **WHEN** an operation lists, gets, sets, or removes a project feature flag
- **THEN** it SHALL continue to use the bound project's configuration
- **AND** it SHALL NOT treat that flag as process-global state

### Requirement: Effective feature-flag resolution

When a feature flag is available at both project and global scope, the effective
value for a bound project SHALL use the project value. When it is absent from
the project, the global value SHALL apply; when absent from both, no value is
resolved.

#### Scenario: Project flag overrides global flag

- **WHEN** a flag has both a project value and a global value
- **THEN** the bound project resolves the project value

#### Scenario: Global flag is the fallback

- **WHEN** a flag has no project value and has a global value
- **THEN** the bound project resolves the global value

### Requirement: Global structured OpenSpec state flag
The system SHALL store machine-wide OpenSpec CLI state in the global-only
`openspec-state` feature flag. Its mapping SHALL contain `validated` as
`"true"` or `"false"`, optional `version` as a version string, and optional
`checked` as a decimal UTC Unix timestamp string.

#### Scenario: Read absent OpenSpec state
- **WHEN** the global `openspec-state` flag is absent
- **THEN** OpenSpec consumers SHALL treat CLI validation and version as unknown
- **AND** reading it SHALL NOT persist a flag

#### Scenario: Set a completed OpenSpec check
- **WHEN** OpenSpec availability and version have been checked
- **THEN** the system SHALL replace the complete global `openspec-state` flag
  through the existing global feature-flag set API
- **AND** a valid result SHALL include `validated`, `version`, and `checked`
- **AND** an invalid result SHALL set `validated` to `"false"`, omit `version`,
  and include `checked`

### Requirement: OpenSpec feature-flag scopes
The `openspec` flag SHALL be project-only and is the exclusive OpenSpec
enablement gate. The `openspec-state` flag SHALL be global-only.

#### Scenario: Global state does not enable a project
- **WHEN** global `openspec-state` is present and a Project does not set
  `project_flags.openspec` to an enabled value
- **THEN** OpenSpec SHALL remain disabled for that Project
- **AND** flag resolution SHALL not use a global `openspec` fallback

### Requirement: Feature-flag mutation authorisation
When provider-backed policy is active for a remote caller, project feature-flag
mutation SHALL require `user` and global feature-flag mutation SHALL require
`admin`. Reading or listing flags SHALL retain existing access
behaviour unless a separate requirement classifies it as protected. When no
provider is selected, remote callers SHALL retain existing behaviour. Stdio
callers SHALL retain unrestricted feature-flag access.

#### Scenario: Caller mutates a global feature flag
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** an admin-scoped caller sets or removes a global feature flag
- **THEN** the system SHALL apply the existing validation and persistence rules
- **AND** it SHALL persist the requested mutation

#### Scenario: Caller cannot mutate a global feature flag
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** a caller lacks the required scope for global feature-flag mutation
- **THEN** the system SHALL return the corresponding authentication or
  authorisation result
- **AND** it SHALL not change global feature-flag configuration

#### Scenario: Caller mutates a project feature flag
- **GIVEN** provider-backed policy is active for the remote caller
- **WHEN** a user-scoped caller sets or removes a bound project's feature flag
- **THEN** the system SHALL apply the existing project-flag validation and
  persistence rules

### Requirement: Default feature-flag normalisation

An unregistered feature flag SHALL accept boolean and string values only. Its
normaliser SHALL preserve arbitrary strings, except for canonical boolean-like
strings, which it SHALL coerce to booleans.

#### Scenario: Generic boolean flag remains boolean

- **WHEN** an unregistered feature flag is set to `true`
- **THEN** the stored feature flag value is the boolean `true`

#### Scenario: Canonical boolean string is coerced

- **WHEN** an unregistered feature flag is set to the string `"false"`
- **THEN** the stored feature flag value is the boolean `false`

#### Scenario: Generic arbitrary string is preserved

- **WHEN** an unregistered feature flag is set to `"custom-mode"`
- **THEN** the stored feature flag value remains that string

#### Scenario: Unsupported generic structured value is rejected

- **WHEN** an unregistered feature flag is set to a list or dictionary
- **THEN** the feature-flag operation rejects the value as invalid

### Requirement: Registered feature-flag normalisation

A flag with a registered validator or normaliser SHALL use that registration
instead of the default scalar path.

#### Scenario: Registered path flag uses its normaliser

- **WHEN** `path-documents` is set to `"docs"`
- **THEN** its registered path normaliser determines the stored value

#### Scenario: Registered workflow flags use their own validation

- **WHEN** `workflow`, `workflow-file`, or `workflow-consent` is set through a
  feature-flag API
- **THEN** its registered validator and normaliser determine whether the value
  is accepted
- **AND** the generic default validator does not override that result

#### Scenario: Workflow-file value is resolved safely

- **WHEN** `workflow-file` is set to a supported path expression
- **THEN** its registered resolver substitutes supported project variables
- **AND** validates the resulting path using the shared filesystem policy

### Requirement: Feature-flag requirement evaluation

Frontmatter `requires-<flag>` declarations SHALL be evaluated against the
effective, normalised value for `<flag>`. Boolean requirements SHALL compare
truthiness, scalar requirements SHALL compare exact values, and list
requirements SHALL match when any required value is present in an actual list
or dictionary key.

#### Scenario: Boolean requirement uses a normalised flag

- **WHEN** a template declares `requires-example: true`
- **AND** the effective normalised `example` flag is truthy
- **THEN** the requirement is satisfied

#### Scenario: List requirement matches a list-valued flag

- **WHEN** a template declares `requires-feature: [alpha, beta]`
- **AND** the effective normalised `feature` flag contains `beta`
- **THEN** the requirement is satisfied

#### Scenario: List requirement matches a dictionary-valued flag

- **WHEN** a template declares `requires-feature: [alpha, beta]`
- **AND** the effective normalised `feature` flag is a dictionary containing
  key `alpha`
- **THEN** the requirement is satisfied
