## 1. Global OpenSpec configuration

- [ ] 1.1 Add the typed global OpenSpec state model and remove deprecated OpenSpec fields from `Project`; verify model serialisation and default-value tests cover the new top-level shape.
- [ ] 1.2 Extend `ConfigManager` to load, save, and expose global `openspec.validated`, `openspec.version`, and `openspec.checked`; verify configuration round-trip tests preserve the exact YAML structure.
- [ ] 1.3 Implement legacy per-project OpenSpec migration, including unambiguous and conflicting versions; verify migration tests remove deprecated project fields and force the next check by leaving `checked` null.

## 2. OpenSpec consumers

- [ ] 2.1 Refactor OpenSpec task and template-context consumers to read global OpenSpec state instead of project fields; verify existing OpenSpec context and task tests pass with the new state source.
- [ ] 2.2 Implement the rolling 24-hour version-check guard using UTC Unix timestamp floats, recording both successful and invalid responses; verify task tests cover absent, expired, recent, valid, and invalid check responses.
- [ ] 2.3 Update project command templates to render global OpenSpec validation and version information; verify rendered-template tests demonstrate that a project switch retains the same CLI state.

## 3. Complete project cloning

- [ ] 3.1 Extend `clone_project` to preserve destination identity while copying project flags, permission paths, additional read paths, and exports; verify clone integration tests retain every transferable source setting.
- [ ] 3.2 Implement and test documented merge and replacement semantics, including source-wins mapping conflicts and source replacement of permission/read-path lists.

## 4. Verification

- [ ] 4.1 Run the relevant configuration, project-tool, OpenSpec-task, and template tests in the foreground; verify all pass.
- [ ] 4.2 Run the full project test suite and `openspec validate fix-clone-and-openspec --strict --no-interactive`; verify both complete successfully.
