# Proposal

## Why

Export tracking exists to let a client use an indexed local copy of Guide
content instead of asking Guide to render it again. It persists client paths,
timestamps, and source hashes in the project even though Guide neither writes
nor controls those client files. The client ecosystem no longer makes that
optimisation worth its permanent state and client-specific path conventions.

## What Changes

- Make `export_content` a stateless content hand-off: render the requested
  content, preserve its delivery frontmatter, and return it for the client to
  write or index at its chosen destination.
- **BREAKING** Remove persisted export destination, timestamp, and metadata-hash
  tracking from the project model and configuration format. Existing `exports`
  configuration is ignored on load and omitted when next saved.
- **BREAKING** Remove the `list_exports` and `remove_export` tools and their
  `guide://_export/list` and `guide://_export/remove` commands.
- **BREAKING** Retire `path-export`, default export paths, and agent-specific
  knowledge-directory selection. An export destination is a client concern and
  Guide will not resolve, approve, or remember it.
- Ensure ordinary content retrieval always returns Guide-rendered content; it
  will no longer return a reference to an earlier client-side export.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `knowledge-export`: make content export a non-mutating client hand-off and
  remove persisted export-tracking behaviour and interfaces.

## Impact

- Affects the content tools, project model and configuration serialisation,
  export command templates, path feature flags, template context, and developer
  and user documentation.
- Removes export-tracking tests and replaces them with behaviour tests proving
  that exports and ordinary content retrieval do not change project state.
- The resulting export operation does not assert access to, ownership of, or
  control over the client filesystem.
