## Context

Aliases are currently treated as alternate path names only. Frontmatter can
declare aliases, and canonical command usage strings can already express query
parameters, but alias resolution does not propagate query strings from alias
definitions into the final canonical command invocation.

That is the core limitation this change addresses.

The required behavior is generic:

- any alias in any command file may include a query string
- the alias lookup name is the alias path without the query suffix
- the alias query string is parsed into implied kwargs
- those implied kwargs are merged into the canonical resolved command

The first proving case should be deliberately small:

- canonical command path: `guide://_project/project`
- alias form: `guide://_project`
- alias-implied kwarg: `verbose=true`

This validated the generic mechanism without coupling the design to handoff.
That proof step is now complete, so handoff can be reintroduced as a consumer
of the same mechanism without expanding the underlying design.

## Goals / Non-Goals

**Goals:**
- Support alias metadata that contributes implied kwargs during alias
  normalization
- Make alias query propagation work generically for any command alias
- Keep canonical commands as the single source of execution and validation
- Preserve explicit caller-supplied kwargs alongside alias-implied kwargs
- Apply the proven generic mechanism to handoff via template aliases only

**Non-Goals:**
- Adding command-specific alias resolution logic
- Creating special-purpose parsing rules for `project`, `handoff`, or any other
  command
- Expanding alias metadata beyond query-string-driven implied kwargs in this
  change
- Reworking handoff validation, path handling, or file behavior

## Decisions

### Extend alias metadata to carry implied kwargs

Alias frontmatter should support query-style suffixes, for example
`project?verbose` or `foo/bar?table&verbose=true`. Alias parsing should separate
the lookup name from the query-string payload, parse that payload using the
same normalization rules as command URIs, and merge the result into the
canonical command invocation during normalization.

This keeps alias behavior generic and template-driven. The alias mechanism
provides defaults, while canonical command execution continues to own final
behavior.

Alternative considered:
- Add command-specific handling for handoff or project. Rejected because it
  would hard-code individual command semantics into generic infrastructure.

### Resolve aliases through shared generic metadata

Alias-aware resolution should operate on shared normalized alias metadata rather
than on raw frontmatter strings scattered across discovery, prompt execution,
help rendering, and guide URI handling.

At minimum, the shared metadata needs to preserve:

- the original alias string for display where useful
- the user-facing alias path used for lookup
- the parsed implied kwargs derived from the alias query string

This avoids duplicating ad hoc query parsing in multiple call paths and makes it
possible to verify that the behavior truly applies to any alias in any command
file.

Alternative considered:
- Parse alias query strings independently in each caller. Rejected because it
  risks drift between prompt commands, help output, and URI resolution.

### Normalize command and URI routing onto the same semantics

The colon command forms and `guide://` URI forms should resolve aliases through
the same normalization rules:

- alias metadata identifies implied kwargs
- implied kwargs are merged with explicit kwargs
- canonical command rendering and validation see the final merged invocation

This reduces the risk of prompt command handling and guide URI handling
drifting into different edge-case behavior.

Alternative considered:
- Implement URI aliases independently from prompt-command aliases. Rejected
  because the behavior is conceptually identical and should stay synchronized.

### Use project as the proof case, then extend handoff by template only

The first command template change should be limited to a small proof case in
`_commands/project/project.mustache`:

- canonical path remains `project/project`
- alias `project?verbose` enables `guide://_project` and `:project` to imply
  verbose mode

This was explicitly a validation target for the new generic mechanism, not a
special rule in the implementation.

With that proof complete, handoff should now be added by updating
`_commands/handoff.mustache` frontmatter only:

- `save-context?write` for the write-oriented alias
- `restore-context?read` for the read-oriented alias

The canonical command stays `_handoff`, and the existing mustache validation
continues to decide whether the final merged kwargs are valid.

Alternative considered:
- Add a second round of command-specific infrastructure for handoff. Rejected
  because the point of the proof case was to avoid exactly that.

## Risks / Trade-offs

- [Alias routing diverges between prompt commands and guide URIs] -> Route both
  through shared normalized alias metadata and merged-kwargs behavior
- [Alias parsing becomes inconsistent across discovery, help, and URI
  resolution] -> Normalize alias query parsing in shared infrastructure instead
  of ad hoc string handling
- [Help output becomes noisy because aliases contain query suffixes] ->
  Preserve user-facing alias names separately from raw alias strings for
  display and lookup
- [Handoff adoption reveals a hidden infrastructure gap] -> Treat any need for
  code changes beyond `_commands/handoff.mustache` as evidence the generic
  mechanism is incomplete and review before proceeding
- [Alias-driven handoff behavior bypasses canonical validation] -> Route the
  aliases through `_handoff` exactly as if the kwargs had been supplied
  explicitly

## Migration Plan

No data migration is required.

Implementation rollout should:

1. Extend alias metadata parsing to support query strings generically
2. Introduce or reuse shared alias normalization that returns:
   - canonical command path
   - alias lookup name
   - alias-implied kwargs
3. Apply that normalization in both prompt-command execution and guide URI
   command resolution
4. Add generic tests before updating any command template
5. Update the `project` alias to imply `verbose`
6. Re-run tests and review the generic mechanism
7. Update `_commands/handoff.mustache` aliases to imply `read` and `write`
8. Add handoff-focused verification on top of the generic path
9. Re-run tests and stop for review

Rollback is straightforward: remove query-bearing alias support and retain plain
alias-path behavior.

## Open Questions

- Should help display show the raw alias string (`project?verbose`) or the
  user-facing alias name (`project`) when alias-implied kwargs exist?
- Should alias query parsing reuse the URI parser directly, or should the
  shared logic be extracted so both URI parsing and alias normalization depend
  on the same lower-level query parser?
- If handoff works with template-only alias changes, should that be treated as
  the reference pattern for future alias-based command ergonomics?
