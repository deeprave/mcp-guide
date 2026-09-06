## ADDED Requirements

### Requirement: Client-aware inherited-PWD bootstrap
The opt-in inherited-PWD bootstrap SHALL use the configured client-path
resolution contract. It SHALL not bind a project from inherited `PWD` unless
that value is valid for the configured client filesystem state.

#### Scenario: Separate filesystem inherited PWD
- **WHEN** inherited-PWD bootstrap is enabled but client filesystems are separate or unconfigured
- **THEN** the request adapter SHALL not bind a project from the Guide process `PWD`
- **AND** the interaction SHALL remain unbound until the client supplies a valid absolute project path
