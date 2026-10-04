# Design

## Context

`export_content` currently returns rendered content but also records a
client-side destination and source hash in the bound project. That record
causes later `get_content` calls to return a reference to a presumed local file
instead of rendered content. It also expands the project's write permissions
for a write which Guide does not perform. See [proposal.md](proposal.md) for
the motivation and the knowledge-export delta for the required behaviour.

## Goals / Non-Goals

**Goals:**

- Preserve `export_content` as a convenient way to obtain rendered content with
  its resolved delivery frontmatter.
- Make exports independent of client filesystem visibility and agent-specific
  knowledge indexing conventions.
- Remove all export-derived project state and the state-dependent content
  delivery branch.
- Preserve configured write-path restrictions without granting new paths.
- Remove all active text and instruction dependencies on tracked exports,
  including indirect guidance to substitute an export for content retrieval.
- Load legacy configuration safely so upgrading does not make projects
  unreadable.

**Non-Goals:**

- Writing, deleting, indexing, checking, or otherwise managing a client file.
- Replacing content retrieval, changing content dispositions, or designing an
  alternative knowledge-index integration.
- Introducing an authentication rule for exporting; any future content-read
  policy must apply consistently to all equivalent content interfaces.

## Decisions

### Validate configured destinations without controlling the client filesystem

`export_content` remains a non-mutating content-rendering operation. The client
supplies the destination; Guide checks it against the bound project's existing
`allowed_write_paths` before returning an export hand-off. A denied path causes
the export to fail, not an automatic permission update. Changing permission
paths remains a separate admin-scoped operation when authentication is active.

Validation applies the configured path policy; it does not resolve a client
path against the server's filesystem or verify client-side existence, symlinks,
writability or successful creation. The client still performs and owns the write.
No agent-specific default directory is selected and no destination is remembered.

The shared project write-list validator rejects filesystem roots, including
lexically equivalent POSIX roots, Windows drive roots and UNC share roots,
regardless of the server platform. This prevents configuring unrestricted
filesystem coverage through a root entry.

Before checking membership or building delivery instructions, export rejects
ASCII control characters (including DEL) and backticks in the destination.
Every destination denial returns a fixed security error without echoing the
rejected path, so an invalid destination cannot introduce agent instructions
through either the success hand-off or its failure message. Spaces, Unicode
filenames and existing permitted destination forms remain supported.

The shared write-path validator currently permits safe temporary locations
without an explicit configured path. Export must not mistake that general
exception for membership of `allowed_write_paths`: its destination must actually
be covered by a configured file or directory entry. This does not change the
shared policy for other operations.

An alternative was retaining default directories and `path-export` as
convenience settings. That still couples project configuration to client
environment conventions and provides little value once Guide no longer tracks
the result, so it is removed.

### Remove the export-state model as a whole

Remove the `Project.exports` model field and its serialisation, metadata hash
calculation, staleness reporting, export listing/removal tools, command
templates, and the `get_content` branch that returns export references. This
avoids retaining an unreachable partial state model.

The export-list display-option helper has no remaining production consumers;
remove it and its utility tests rather than retain dead code or suppress the
unused-code check. Mark its former ADR convention superseded.

Existing YAML may contain `exports`. Loading must discard that field before
constructing the project model; saving naturally omits it. No migration write
is required solely to remove it.

### Keep delivery frontmatter

The export frontmatter remains because it travels with the returned payload and
allows a client that does index it to preserve Guide's content type and handling
instruction. It is not export tracking.

### Remove instruction dependencies, not just the data model

Audit tool argument descriptions/docstrings, result instructions, command and
system templates, feature-flag/template-context documentation, URI examples and
developer diagrams. Remove references to tracked destinations, timestamps,
source hashes, stale/current exports, export-cache bypass, automatic permission
grants and reuse of an indexed/local copy instead of Guide content retrieval.
Preserve ordinary export instructions and their delivery frontmatter, but not
instructions that depend on knowing whether an earlier export exists.

Concrete current references include `ContentArgs.force` and `get_content`'s
docstring in `tools/tool_content.py`, `_system/_export.mustache`,
`_system/_exports-format.mustache`, `_commands/export/add.mustache`, and the
export sections of user content-management, command, document, feature-flag and
Guide-URI documentation. The add command needs revised destination guidance
even though it remains available. Keep client create/overwrite instructions
distinct from the retired metadata/hash-based skip or reuse behaviour.

For the same expression and pattern, `get_content` and equivalent content URIs
continue to return Guide-rendered content regardless of an earlier export or
legacy tracking entries. No returned instruction should tell an agent to use
an exported/indexed file as a substitute for requesting that content from Guide.
Unrelated language-module exports and historical change records are not targets
for a mechanical deletion of the word "export".

### Reconcile authentication with the stateless operation

Remove the temporary `user` gate on `export_content` when its configuration
writes are removed, and retire `remove_export` entirely. Update ADR-014 and the
canonical authentication specification through this change, not the archived
`add-mcp-authentication` artefacts. Destination validation is independent of
authentication; having admin scope does not disable configured export paths.

## Risks / Trade-offs

- [Clients rely on stale-export references to avoid large repeated payloads] →
  They receive rendered content on every request; clients that need caching own
  their own cache and invalidation strategy.
- [Clients call removed tools or commands] → Treat their absence as a deliberate
  breaking API removal and document the replacement: call `export_content` and
  manage the resulting file locally.
- [Legacy project configuration retains old metadata] → Ignore it during load
  and omit it on normal future saves without making configuration loading fail.

## Migration Plan

1. Remove the state model, serialisation, and state-dependent content delivery.
2. Make `export_content` return the rendered payload and client-supplied
   destination after configured write-path validation, without default-path
   selection or configuration updates.
3. Remove retired interfaces and audit all active instructions/text for indirect
   tracking dependencies, while retaining destination-policy guidance.
4. Add behavioural tests for stateless export, legacy configuration loading,
   and ordinary content retrieval after an export request.

Rollback is a normal release rollback. The removed state is only an optimisation
record; it is not needed to preserve project content or configuration.
