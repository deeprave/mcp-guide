# client-path-resolution Specification

## Purpose

Define verified client filesystem sharing and client-aware project path resolution.

## Requirements

### Requirement: Global verified client filesystem state
LazyPath SHALL own process-wide sharing state initially None. Only a successful
stdio filesystem probe SHALL set True. HTTP/HTTPS SHALL set False and SHALL NOT
probe. None and False SHALL disable client shorthand. State SHALL NOT persist
across server restarts.

#### Scenario: Unverified stdio
- **WHEN** stdio starts without a completed probe
- **THEN** sharing SHALL be None and client shorthand SHALL be rejected

#### Scenario: HTTP client on any host
- **WHEN** HTTP or HTTPS serves an interaction
- **THEN** sharing SHALL remain disabled regardless of client location
- **AND** no probe file or probe instruction SHALL be created

### Requirement: Client resolution on LazyPath
Client path resolution SHALL be implemented by LazyPath.client_resolve().
Verified sharing SHALL permit ordinary server-side ~, ~user, environment and
filesystem resolution. Matching filesystems SHALL be sufficient; client metadata
MAY corroborate the same-user assumption but SHALL NOT be a required gate.

#### Scenario: Verified stdio shorthand
- **WHEN** a verified stdio interaction supplies ~, ~user or a variable-bearing path
- **THEN** LazyPath SHALL resolve it using server user/environment semantics

#### Scenario: Relative switch
- **WHEN** verified stdio switches to a relative root
- **THEN** it SHALL resolve relative to the currently bound root

#### Scenario: Unverified or disabled shorthand
- **WHEN** sharing is None or False and client input is relative, user-anchored or contains a variable reference
- **THEN** it SHALL reject the input and request an absolute client path

#### Scenario: Absolute unshared root
- **WHEN** sharing is None or False and an absolute client path is supplied
- **THEN** it SHALL normalise lexically without environment expansion or server symlink resolution

### Requirement: One-shot filesystem probe
After initial absolute-root binding on unverified stdio, one task SHALL exclusively
create a uniquely named .mcp-guide-fs-probe-<random-id> file with unpredictable
contents, queue an instruction to read its exact path and return via
send_file_content, and intercept only that registered response before ordinary
file handling. Expected contents SHALL NOT be disclosed in the instruction.
There SHALL be at most one global pending attempt.

#### Scenario: Matching probe
- **WHEN** the owning task receives the exact probe path and matching contents
- **THEN** it SHALL consume the response and record shared state True

#### Scenario: Unrelated file
- **WHEN** a file response does not match the exact registered path
- **THEN** the probe SHALL NOT consume it or treat it as verification

#### Scenario: Probe failure
- **WHEN** creation, reading or content verification fails
- **THEN** sharing SHALL remain disabled without failing the bound project

### Requirement: Dispatch-based probe timeout and cleanup
The task SHALL use queued-instruction dispatch notification to start an
approximately 60-second response timeout only after outgoing-response dispatch notification.
Finalisation SHALL remove its probe file, queued/tracked instruction and
subscriptions on result, timeout or Session disposal. No recurring verification
or automatic retry SHALL remain after completion.

#### Scenario: Instruction waits in queue
- **WHEN** an instruction has been queued but not attached to an outgoing response
- **THEN** the response timeout SHALL NOT run

#### Scenario: Delivered instruction times out
- **WHEN** approximately 60 seconds elapse after outgoing-response dispatch notification without a valid response
- **THEN** the task SHALL record False and clean up its owned resources

#### Scenario: Session disposed before completion
- **WHEN** the probe-owning Session is disposed of
- **THEN** pending probe resources SHALL be removed and expansion SHALL not become enabled

#### Scenario: Verification completes
- **WHEN** the probe reaches a terminal result
- **THEN** the task SHALL remove its file and instruction and unsubscribe
