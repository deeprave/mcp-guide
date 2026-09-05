## 1. Public project-switch contract

- [ ] 1.1 Extend `SwitchProjectArgs` so `name` and `path` are independently optional but at least one is required; retain name-only compatibility and verify the advertised MCP schema and argument-validation tests.
- [ ] 1.2 Update the `switch_project` tool response and public description to state that `path` rebinds the project root, and document name-only, path-only, and combined selection; verify integration tests cover each successful form, missing-selection failure, and advertised description.

## 2. Session root transition

- [ ] 2.1 Implement lexical switch-path normalisation: expand `~` and `~user`, retain absolute paths, and resolve relative paths against the current bound root while normalising `.` and `..`; verify focused unit tests do not require target filesystem existence.
- [ ] 2.2 Add an atomic Session root-and-project switch path that preserves the session owner and session ID, derives the basename configuration for path-only selection, and uses an explicit name when supplied; verify same-name/different-root identities remain independent.
- [ ] 2.3 Preserve `set_project` as initial-binding-only and reject an unbound relative root switch; verify existing second-bind protection and new no-base error behaviour.

## 3. Project-scoped lifecycle refresh

- [ ] 3.1 Ensure a successful root switch emits the project-change lifecycle even when the configuration name is unchanged; verify template context, resolved flags, queued instructions, and project tasks are refreshed for the new root.
- [ ] 3.2 Ensure filesystem-facing operations use the switched root and active configuration publication follows the new `(name, root_hash)` identity; verify focused session and integration tests.
