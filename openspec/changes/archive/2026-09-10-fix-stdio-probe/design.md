## Context

See [proposal.md](proposal.md) for motivation. The existing probe starts after
an absolute stdio root is bound, creates a secret file below that root, asks the
client to return its content, and enables shared-filesystem shorthand only on
an exact matching response. Until then, client paths deliberately retain lexical
semantics.

## Goals / Non-Goals

**Goals:**

- Keep initial client-root binding free of server-initiated filesystem mutation.
- Preserve the existing conservative verification lifecycle: one global attempt,
  exact response matching, dispatch-based timeout, and clean-up.
- Treat a probe that cannot be read by the client as unshared without rejecting
  the already-bound project.

**Non-Goals:**

- Establishing that every client-selected project root is writable by the server.
- Changing client path parsing, project identity, or HTTP/HTTPS probe policy.
- Retrying verification or adding a user-configurable probe location.

## Decisions

### Create the challenge directly beneath the shared `/tmp` base

The probe will exclusively create a randomly named file directly beneath the
server's system-wide `/tmp` directory. The Guide server owns the file, writes
the unpredictable challenge before it is announced, and explicitly grants read
permission on that file so a client sharing the server filesystem can read it.
It SHALL NOT create a private per-user temporary directory, a probe subdirectory,
or modify `/tmp` or any ancestor permissions. The task retains the exact created
path as its sole clean-up target.

This proves that the client can read a server-owned path from the shareable base,
which is the required precondition before server filesystem path expansion can
stand in for client semantics. If this conservative check fails in a containerised
or remote setup, the established absolute-path-only behaviour remains available.

Using the client project root is rejected because it performs a write before
the root has been verified. Requiring a pre-verified shared root is rejected
because no such independent trust signal currently exists and would make the
initial handshake circular.

### Keep the event protocol and terminal behaviour unchanged

The instruction will still request only an existing-file read and an exact
`send_file_content` response. The task will accept only its registered path and
challenge, consume only that matching event, and set sharing to `False` for a
wrong response, timeout, creation error, or disposal. Completion removes the
server-owned file and task resources exactly once.

This avoids broadening the client-facing protocol and prevents an unrelated file
content event from enabling shorthand.

## Risks / Trade-offs

- A shared project directory can be visible while `/tmp` is not → Treat the
  filesystem as unshared and preserve portable absolute-path operation; do not
  fall back to writing beneath the client root.
- Temporary-file removal can fail during cancellation or process termination →
  Use an exclusively created, tracked file and make normal, timeout, and
  disposal clean-up idempotent.
- A client can return arbitrary content for the announced path → Keep the secret
  unpredictable and require the exact path and contents before enabling sharing.

## Migration Plan

1. Replace client-root probe creation with server-owned temporary-file creation.
2. Update focused async task tests to assert the selected root remains untouched
   throughout success, mismatch, timeout, and disposal paths.
3. Run the client-resolution test module and the relevant full test selection.

No data migration or compatibility flag is required. Rolling back restores the
prior handshake behaviour, though it reintroduces the avoided unverified-root
write.
