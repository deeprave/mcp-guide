# Spec Delta

## ADDED Requirements

### Requirement: Prompt command authorisation boundary

The Guide prompt command route SHALL apply an `AuthScope` only when the selected
command directly performs a server-side operation requiring that scope. A command
that only reads state, renders content, queues session-local work, or instructs the
client to invoke a separately protected tool SHALL remain available without
authentication. A command template SHALL NOT define or weaken the required scope.

#### Scenario: Prompt command renders guidance for a protected tool

- **WHEN** authentication is active and an unauthenticated caller invokes a prompt
  command that only renders guidance to use a protected tool
- **THEN** the command SHALL render its guidance
- **AND** the later protected tool invocation SHALL remain responsible for its own
  authorisation decision

#### Scenario: Prompt command performs a protected operation

- **WHEN** authentication is active and an unauthenticated caller invokes a prompt
  command with a server-owned `user` or `admin` scope declaration
- **THEN** the prompt SHALL return the corresponding authentication-required result
- **AND** it SHALL not perform the protected operation
