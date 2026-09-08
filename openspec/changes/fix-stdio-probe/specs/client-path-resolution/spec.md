## MODIFIED Requirements

### Requirement: One-shot filesystem probe
After initial absolute-root binding on unverified stdio, one task SHALL
exclusively create a uniquely named probe file with unpredictable contents
directly beneath the server's system-wide `/tmp` shareable base. It SHALL grant
read permission on that file without modifying `/tmp` or any ancestor directory.
It SHALL queue an instruction to read that exact path and return its contents via
`send_file_content`, and intercept only that registered response before ordinary
file handling. Expected contents SHALL NOT be disclosed in the instruction. The
probe SHALL NOT create, modify, or remove a file below the caller-supplied
project root while sharing remains unverified. There SHALL be at most one global
pending attempt.

#### Scenario: Matching probe
- **WHEN** the owning task receives the exact server-owned `/tmp` probe path and matching contents
- **THEN** it SHALL consume the response and record shared state True

#### Scenario: Unrelated file
- **WHEN** a file response does not match the exact registered path
- **THEN** the probe SHALL NOT consume it or treat it as verification

#### Scenario: Unverified root remains untouched
- **WHEN** initial stdio binding starts filesystem-sharing verification for an unverified client root
- **THEN** the probe SHALL not create, modify, or remove any path below that root

#### Scenario: Probe failure
- **WHEN** creation, reading or content verification fails
- **THEN** sharing SHALL remain disabled without failing the bound project

### Requirement: Dispatch-based probe timeout and cleanup
The task SHALL use queued-instruction dispatch notification to start an
approximately 60-second response timeout only after outgoing-response dispatch notification.
Finalisation SHALL remove its server-owned probe file, queued/tracked instruction and
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
- **THEN** the task SHALL remove its server-owned `/tmp` file and instruction and unsubscribe
