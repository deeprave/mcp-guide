# Spec Delta

## ADDED Requirements

### Requirement: Command URI authorisation equivalence

The `guide://_...` command URI route, including the `read_resource` tool's command
URI resolution, SHALL apply the same server-owned command `AuthScope` decision as
the equivalent Guide prompt command. The command template and URI form SHALL NOT
define or weaken the required scope.

#### Scenario: Protected command URI has no user access

- **WHEN** authentication is active and an unauthenticated caller resolves a command
  URI for a command that directly performs a user-protected server operation
- **THEN** the command URI route SHALL return the authentication-required result
- **AND** it SHALL not perform the protected operation

#### Scenario: Guidance-only command URI

- **WHEN** authentication is active and an unauthenticated caller resolves a command
  URI for a command that only returns guidance or invokes no server-side protected
  operation
- **THEN** the command URI route SHALL return the command output without requiring
  authentication
