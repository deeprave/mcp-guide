## Context

Client roots currently reuse server-side LazyPath expansion. The approved policy
makes verified shared stdio filesystems the exception and disables all shorthand
over HTTP/HTTPS, irrespective of where any individual HTTP client runs.

## Decisions

### Global tri-state in LazyPath

LazyPath owns process-wide sharing state: None initially/unverified, True after
successful stdio verification, False when disabled or verification fails. Falsy
state always rejects client shorthand. HTTP/HTTPS sets False and never probes.
Stdio initialises None and schedules one verification attempt after its first
successful absolute-root binding. Do not persist this result or infer success
from stdio alone, matching paths, existing files, or client names.

### Resolution remains on LazyPath

Add client_resolve() to LazyPath rather than a separate resolver implementation.
True delegates to ordinary resolve(), including ~, ~user and environment
expansion. Relative switch paths are joined to the currently bound root first,
not the server working directory. Initial binding still requires an absolute
path, including after permitted user/environment expansion when verified. Never
use server CWD to make relative initial input absolute. Absolute parent components
are normalised rather than rejected. False/None requires absolute input, rejects user anchors
and variable references, and lexically normalises without filesystem access.
URI decoding remains at the project-input boundary, before policy enforcement.

A successful probe is sufficient assurance for all three conveniences. Available
client information may corroborate the result but is not an additional gate.
Assume the same user/home otherwise. Server environment values are used; this is
an explicit convenience trade-off, not proof of identical process environments.

### One-shot verification task

Integrate with existing Session task ownership, queued acknowledged instructions,
file-content events and timer handling. Reserve a single global pending attempt
so more than one stdio Session cannot start competing probes.

Create .mcp-guide-fs-probe-<random-id> directly under the first bound absolute
project root, using exclusive creation and unpredictable contents. Never
overwrite an existing file or include the expected contents in the instruction.
Ask the agent to read the exact absolute file path and submit its contents via
send_file_content. Failure to create the probe records False without blocking
the project binding.

Match the exact registered path, not a filename prefix, and consume the response
before document ingestion or unrelated file consumers. Only the owning task may
complete the pending attempt. Compare returned contents with the challenge.
Matching contents records True; mismatch/read failure records False.

### Dispatch-based timeout and finalisation

Queue one instruction using the existing acknowledgement mechanism. Do not start
the response timeout at task construction, file creation or queue insertion.
Start a 60-second monotonic timeout when the instruction is attached to an
outgoing response. This dispatch notification is distinct from the existing
result acknowledgement and does not confirm client receipt. Time spent waiting
in the queue does not count towards the response timeout.

On success, failure or timeout, record the global result, remove only the probe
file created by this task, clear its queued/tracked instruction and unsubscribe.
Session disposal/cancellation also cleans up the owned file and subscriptions.
No recurring verification task or automatic retry remains after completion.
Do not let an unfinished probe on an expiring Session enable state from an
unrelated later file reply.

### Binding, identity and server paths

Gate inherited-PWD bootstrap on verified sharing, avoiding server-PWD binding
before verification; an explicit initial absolute client root remains available.
Use the client resolver at client root boundaries. Shared resolution may follow
server symlinks; unverified/separate root identity stays lexical. Leave
server-owned config, docroot and installation resolution unchanged.

### Documentation

Update installation, protocol/session, project-selection and agent guidance.
Explain initial absolute binding, stdio verification, pending/failed states,
dispatch-based timeout, user/environment assumptions, and server-owned paths.
Document that Docker stdio needs successful verification and ordinary unshared
container deployments lack shorthand. HTTP/HTTPS always lacks shorthand and
never probes, including localhost HTTP and HTTP from Docker or another host.

## Risks and Non-Goals

The challenge checks shared access, not a hostile client's honesty or equivalence
of all mounts/users/environments. Read-only roots can fail verification safely.
Do not add per-HTTP-session sharing, Docker heuristics, global user/environment
comparison, automatic retries or a new configuration subsystem.
