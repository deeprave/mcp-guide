## Context

See proposal.md for the motivation. A retained Guide Session currently records an
immutable client root and separately allows a configuration-name switch at that
root. The root is used by project identity, filesystem policy, rendering, and
project-scoped task lifecycle, so a root change must not expose a mixed state.

## Goals / Non-Goals

**Goals:**

- Add an additive `path` option to `switch_project` while keeping name-only
  callers compatible.
- Define deterministic normalisation for absolute, user-anchored, and
  root-relative paths without requiring a client filesystem lookup.
- Reuse the session's existing project-change lifecycle for every successful
  root transition.

**Non-Goals:**

- Changing the initial-binding contract of `set_project`.
- Discovering roots from the client, the server working directory, or MCP roots
  notifications.
- Persisting a Session's root selection across a server restart.
- Changing the session owner or transferring state between sessions.

## Decisions

### Optional path is separate from name

`switch_project` will expose optional `name` and `path` fields, requiring at
least one. `name` retains its meaning as a configuration-name selection;
`path` controls root selection. This preserves existing clients and avoids the
ambiguous parsing and weaker schema documentation of a `name_or_path` field.

When `path` is omitted, existing name-only behaviour remains. When it is present
without `name`, the normalised path basename supplies the name. When both are
present, the requested name is selected at the new root.

### Lexical root-path normalisation

The switch path will first expand `~` and `~user`. An absolute result is used as
the target root. A non-absolute result is joined to the Session's current bound
root, then `.` and `..` are normalised lexically. This does not check target
existence or resolve symlinks: the value remains a declared client-root identity,
not a server filesystem lookup.

An unbound Session has no base for a relative path and therefore receives a clear
validation error. Existing absolute initial binding remains available through
`set_project`.

### Atomic root and project replacement

The Session will use its existing serialisation lock to resolve or create the
target project configuration and then replace the root and project together.
After the replacement, it will issue the same project-change lifecycle used for a
configuration switch. The lifecycle must run even when the configuration name is
unchanged because the root-hash identity has changed.

The listener protocol can continue accepting names for compatibility, but root
transition diagnostics should carry the old and new roots where useful. The
TaskManager's restart path is responsible for clearing project-scoped instructions
and task instances before starting the new root's eligible tasks.

## Risks / Trade-offs

- [A client path may be malformed or escape a parent directory] → normalise it
  before deriving configuration identity, validate its absolute result and
  basename, and never use it for a server-side existence check.
- [A root change with an unchanged name can leave stale state] → test listener
  notification, task replacement, template-cache invalidation, and filesystem
  root use for that exact case.
- [Home expansion differs between a remote client and server] → document that
  the configured Guide process performs `~` and `~user` expansion; clients that
  require a different home mapping must submit an absolute path.

## Migration Plan

The API addition is backwards compatible: existing name-only `switch_project`
calls keep their behaviour. No persisted configuration data changes. Rollback is
the removal of the optional path handling; configurations remain keyed by their
existing name and root hash.
