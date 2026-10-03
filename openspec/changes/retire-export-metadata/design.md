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
- Load legacy configuration safely so upgrading does not make projects
  unreadable.

**Non-Goals:**

- Writing, deleting, indexing, checking, or otherwise managing a client file.
- Replacing content retrieval, changing content dispositions, or designing an
  alternative knowledge-index integration.
- Introducing an authentication rule for exporting; any future content-read
  policy must apply consistently to all equivalent content interfaces.

## Decisions

### Return content, not a server-approved filesystem action

`export_content` remains a content-rendering operation. Its destination is
returned as client-provided context for the hand-off, not interpreted as a path
Guide can resolve or authorise. This reflects the actual boundary for remote
HTTP(S) clients and avoids misleading filesystem assurances for stdio clients.

An alternative was retaining default directories and `path-export` as
convenience settings. That still couples project configuration to client
environment conventions and provides little value once Guide no longer tracks
the result, so it is removed.

### Remove the export-state model as a whole

Remove the `Project.exports` model field and its serialisation, metadata hash
calculation, staleness reporting, export listing/removal tools, command
templates, and the `get_content` branch that returns export references. This
avoids retaining an unreachable partial state model.

Existing YAML may contain `exports`. Loading must discard that field before
constructing the project model; saving naturally omits it. No migration write
is required solely to remove it.

### Keep delivery frontmatter

The export frontmatter remains because it travels with the returned payload and
allows a client that does index it to preserve Guide's content type and handling
instruction. It is not export tracking.

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
   destination without path resolution or configuration updates.
3. Remove retired tools, commands, templates, feature flags, and documentation.
4. Add behavioural tests for stateless export, legacy configuration loading,
   and ordinary content retrieval after an export request.

Rollback is a normal release rollback. The removed state is only an optimisation
record; it is not needed to preserve project content or configuration.
