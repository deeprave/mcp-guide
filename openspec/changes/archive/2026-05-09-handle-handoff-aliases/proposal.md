# Change: handle-handoff-aliases

## Why

Command aliases currently behave as alternate names only. They do not propagate
query-string defaults into the resolved canonical command invocation.

That gap is the real problem to solve. The implementation must be generic:

- if an alias contains a query string, that query string should be parsed
- the parsed values should be merged into the resolved command kwargs
- this should work for any alias in any command file

The generic mechanism is now in place and proven with the `project` alias proof
case. The remaining purpose of this change is to apply that mechanism to the
original handoff workflow.

## What Changes

- Add generic support for aliases that include query strings
- Parse alias query parameters during alias resolution
- Merge alias-implied kwargs into the canonical resolved command invocation
- Preserve explicit caller-supplied kwargs alongside alias-implied kwargs
- Use the `project` alias as the first proof case after the generic mechanism
  and tests are complete
- Update the handoff command aliases so intent-specific entry points imply
  `read` or `write` through frontmatter only

## Explicit Non-Goal

This extension should **not** add any new command-specific infrastructure.
If the generic alias-query implementation is correct, handoff should only
require template updates in `_commands/handoff.mustache`.

## Suggested Approach

The generic alias-query propagation is already implemented and verified.

Then:

- update `_commands/handoff.mustache` to add the original intent-specific
  aliases using query-bearing frontmatter
- preserve the existing canonical `_handoff` behavior and validation rules
- verify that `:save-context`, `:restore-context`, `guide://_save-context/...`,
  and `guide://_restore-context/...` resolve through the canonical handoff
  command
- re-run tests

There must still be no special-case logic for handoff, project, or any other
command.

## Impact

- Affected specs:
  - prompt alias normalization behavior
  - guide:// command URI alias behavior
- Likely affected implementation:
  - command discovery alias metadata handling
  - command alias resolution and normalization
  - guide:// URI alias resolution
  - help and command discovery display logic where aliases are surfaced
  - handoff command template frontmatter
- Deliberately not affected in this extension:
  - generic alias parsing infrastructure
  - handoff validation rules beyond alias-driven default kwargs
