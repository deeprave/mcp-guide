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
  Guide will not select or remember it, but will validate it against the project's existing configured write paths without extending those permissions.
- Ensure ordinary content retrieval always returns Guide-rendered content; it
  will no longer return a reference to an earlier client-side export.
- Audit all active instructions and text, including tool schemas/docstrings,
  command/system templates, documentation and examples, for subtle dependencies
  on tracking. Remove guidance to read, index, reuse or recreate a prior export
  instead of calling `get_content` for the equivalent expression or content URI.
- Reject export destinations outside configured write paths. Do not add a
  destination to `allowed_write_paths` or claim to verify the client filesystem.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `knowledge-export`: make content export a non-mutating client hand-off and
  remove persisted export-tracking behaviour and interfaces while retaining
  configured write-path enforcement.
- `mcp-authentication`: remove the temporary export-metadata scope rule after
  export becomes non-mutating, without bypassing destination policy.
- `content-tools`: replace prior-export reference guidance with current-payload delivery guidance.
- `help-template-system`: retain export/add and its alias, retiring tracking commands and formatting.
- `feature-flag-normalization`: use the retained documents path flag in normalisation examples.
- `guide-project-tools`: remove exports from transferable clone configuration.
- `request-context`: remove exports from the active project data contract.
- `template-system`: remove the retired export system-template example.

## Impact

- Affects the content tools, project model and configuration serialisation,
  export command templates, path feature flags, template context, and developer
  and user documentation.
- Removes export-tracking tests and replaces them with behaviour tests proving
  that exports and ordinary content retrieval do not change project state.
- The resulting export operation does not assert access to, ownership of, or
  control over the client filesystem.
