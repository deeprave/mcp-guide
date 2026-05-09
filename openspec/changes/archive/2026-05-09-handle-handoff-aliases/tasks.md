## 1. Generic Alias Query Propagation

- [x] 1.1 Extend alias frontmatter parsing so aliases can include query strings such as `project?verbose`
- [x] 1.2 Introduce shared normalized alias metadata that separates the lookup alias path from alias-implied kwargs
- [x] 1.3 Merge alias-implied kwargs into the canonical resolved command invocation without any command-specific branches
- [x] 1.4 Update command discovery and help-facing alias handling so alias query suffixes do not break lookup or display

## 2. Generic Verification Before Any Template Change

- [x] 2.1 Add or update prompt-command tests covering alias-implied kwargs, alias name matching without the query suffix, and preservation of explicit kwargs
- [x] 2.2 Add or update guide:// command URI tests covering alias-implied kwargs and merged-kwargs behavior through the same generic resolution rules
- [x] 2.3 Review implementation paths to confirm there is no special handling for `handoff`, `project`, or any other individual command

## 3. Project Alias Proof Case

- [x] 3.1 Update `_commands/project/project.mustache` so the alias implies `verbose` while the canonical command behavior remains unchanged
- [x] 3.2 Add or update tests proving `guide://_project/project` remains the default display path and `guide://_project` resolves through the alias-implied `verbose` behavior
- [x] 3.3 Re-run the relevant test suite and stop for review without changing handoff

## 4. Handoff Alias Adoption

- [x] 4.1 Update `_commands/handoff.mustache` aliases so `save-context?write` and `restore-context?read` adopt the generic alias-query mechanism
