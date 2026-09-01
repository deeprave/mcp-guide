## ADDED Requirements

### Requirement: Resource Application Context Boundary
Guide URI resource and command handlers SHALL use the resolved RequestContext from
their public resource boundary. URI parsing may extract an interaction identifier,
but application handling SHALL use the resulting resolved Session and Project rather
than raw FastMCP context.

#### Scenario: Resource delegates to content or command handling
- **WHEN** a Guide resource request routes to a content or command handler
- **THEN** the delegated operation SHALL receive the same resolved RequestContext
- **AND** it SHALL retain the request's validated interaction ownership and active Project
