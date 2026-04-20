## 1. Generic Alias Implied-Kwargs Support

- [ ] 1.1 Extend alias frontmatter parsing so aliases can include query-style implied kwargs such as `save-context?write`
- [ ] 1.2 Update alias normalization to separate the user-facing alias name from its implied kwargs and merge those kwargs into the canonical command invocation
- [ ] 1.3 Update command discovery and help-facing alias handling so alias query suffixes are parsed or ignored without breaking alias lookup and display

## 2. Handoff Alias Integration

- [ ] 2.1 Add `save-context?write` and `restore-context?read` alias definitions to the canonical handoff command metadata
- [ ] 2.2 Extend guide:// command URI alias resolution so `_save-context` and `_restore-context` use the same alias-implied kwargs behavior as colon commands
- [ ] 2.3 Preserve the existing requirement that handoff aliases still provide a target path and continue to rely on canonical handoff validation for invalid mode combinations

## 3. Verification

- [ ] 3.1 Add or update command parsing tests covering alias-implied kwargs, alias name matching without the query suffix, and preservation of additional explicit kwargs
- [ ] 3.2 Add or update guide:// command URI tests covering alias-implied kwargs, path requirements, and invalid merged mode combinations
- [ ] 3.3 Add or update template-level or integration checks to confirm handoff aliases render through the existing canonical handoff template with merged kwargs
