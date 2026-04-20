## Context

The current handoff flow requires callers to choose an explicit mode before a
path can be processed. That keeps the command precise, but it makes the two
common handoff intents less ergonomic than necessary:

- saving context to a file
- restoring context from a file

This change adds intent-specific aliases for those flows while preserving the
existing handoff implementation as the single place that enforces path and mode
validation. The affected behavior spans both colon-prefixed commands and
`guide://` command URIs, so the design needs to keep command parsing, alias
resolution, help rendering, and URI resolution aligned.

## Goals / Non-Goals

**Goals:**
- Add `save-context` and `restore-context` aliases that imply handoff write and
  read modes respectively
- Support generic alias metadata that can contribute implied kwargs during alias
  normalization
- Preserve the requirement that a concrete target path is still supplied
- Keep `_handoff` as the canonical implementation path so mode handling remains
  consistent across entry points
- Keep error messaging clear when callers omit the path or specify invalid mode
  combinations

**Non-Goals:**
- Changing the underlying file handoff behavior, storage format, or path safety
  rules
- Replacing the explicit `_handoff` command or loosening its validation rules
- Adding broader workflow aliases beyond the save and restore handoff cases

## Decisions

### Extend alias metadata to carry implied kwargs

Alias frontmatter should support query-style suffixes, for example
`save-context?write` and `restore-context?read`. Alias parsing should separate
the display or lookup name from the implied kwargs, then merge those kwargs into
the canonical command invocation during normalization.

This keeps alias behavior generic and template-driven. The alias mechanism
provides defaults, while the canonical command continues to own the final
validation rules.

Alternative considered:
- Add handoff-specific alias handling in the parser and URI router. Rejected
  because it would hard-code one command's semantics into generic command
  infrastructure.

### Keep path handling unchanged and mandatory

Aliases should not alter how handoff target paths are interpreted. They only
remove the need to spell out the mode. The path remains a required argument for
both command and URI entry points, and the final merged kwargs should be passed
to the existing handoff template exactly as if they had been supplied
explicitly.

This keeps alias behavior predictable and avoids creating a partial shorthand
that bypasses core path validation.

Alternative considered:
- Allow aliases without a path and infer a default file. Rejected because the
  proposal explicitly preserves strict path requirements and this would add new
  stateful behavior.

### Normalize command and URI routing onto the same semantics

The colon command forms and `guide://` URI forms should resolve aliases through
the same normalization rules:

- alias metadata identifies implied kwargs
- provided path becomes the canonical command argument
- implied kwargs are merged with explicit kwargs
- canonical command rendering and validation see the final merged invocation

This reduces the risk of the command parser, help system, and URI parser
drifting into different edge-case behavior.

Alternative considered:
- Implement URI aliases independently from command aliases. Rejected because the
  behavior is conceptually identical and should stay synchronized.

## Risks / Trade-offs

- [Alias routing diverges from canonical handoff behavior] -> Route aliases
  through the same final validation and execution path as `_handoff`
- [Alias parsing becomes inconsistent across command discovery, help, and URI
  resolution] -> Normalize alias query parsing in shared infrastructure instead
  of ad hoc string handling
- [URI and command entry points evolve differently] -> Centralize alias-kwargs
  resolution in shared parsing or normalization logic where possible
- [Error messages become less clear because mode is now implicit] -> Ensure
  validation errors mention the alias-implied mode when relevant

## Migration Plan

No data migration is required.

Implementation rollout should:

1. Extend alias metadata parsing to support query-style implied kwargs
2. Update command discovery, help, and URI alias resolution to ignore or parse
   the alias query suffix as appropriate
3. Normalize alias requests into canonical command plus merged kwargs
4. Reuse existing handoff validation and execution
5. Add coverage for success cases, missing path cases, and merged-kwargs
   behavior

Rollback is straightforward: remove alias recognition and retain `_handoff` as
the only supported entry point.

## Open Questions

- Should alias frontmatter continue using query-style shorthand only, or should
  it also gain a structured form for non-boolean implied kwargs in future?
- Should help output display alias query suffixes verbatim or present aliases in
  a cleaner user-facing form while preserving the implied-kwargs behavior?
