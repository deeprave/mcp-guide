# Spec Delta

## MODIFIED Requirements

### Requirement: Client Info Utility Tool
The system SHALL provide a `client_info` utility tool that returns information
about the agent/client environment.

Arguments:
- `verbose` (optional, boolean): include detailed information when available.

The tool SHALL return a Result pattern response containing available agent name,
version, client environment details, and a `protocol` field containing the
established session protocol classification. The protocol
classification SHALL distinguish MCP
`2026-07-28` from `legacy` without exposing a raw negotiated revision as a
substitute for that classification.

#### Scenario: Retrieve client information
- **WHEN** `client_info` is invoked for an established session
- **THEN** it SHALL return available agent name, version, environment details, and
  the session's MCP `2026-07-28` or `legacy` protocol classification
- **AND** the response SHALL use the standard Result pattern
