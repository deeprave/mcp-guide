# Spec Delta

## MODIFIED Requirements

### Requirement: Query Parameter Parsing

The URI parser SHALL parse query parameters as keyword arguments.

Boolean flags without values SHALL default to True.
Boolean flags with explicit values SHALL parse "true" as True and "false" as False.
Non-boolean values SHALL be passed as strings.
Command query options SHALL normalise the standard short aliases: `v`, `h`,
`q`, `f`, `d`, and `t` SHALL mean `verbose`, `help`, `quiet`, `force`,
`debug`, and `table` respectively.

#### Scenario: Boolean flag without value
- **WHEN** URI is `guide://_status?verbose`
- **THEN** kwargs are `{"verbose": True}`

#### Scenario: Boolean flag with true value
- **WHEN** URI is `guide://_status?verbose=true`
- **THEN** kwargs are `{"verbose": True}`

#### Scenario: Boolean flag with false value
- **WHEN** URI is `guide://_status?verbose=false`
- **THEN** kwargs are `{"verbose": False}`

#### Scenario: Short command option
- **WHEN** URI is `guide://_status?v`
- **THEN** kwargs are `{"verbose": True}`

#### Scenario: String value
- **WHEN** URI is `guide://_perm/write-add?path=docs/`
- **THEN** kwargs are `{"path": "docs/"}`

#### Scenario: Multiple query params
- **WHEN** URI is `guide://_openspec/show?change=enable-codex-integration&verbose=true`
- **THEN** kwargs are `{"change": "enable-codex-integration", "verbose": True}`
