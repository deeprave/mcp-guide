## 1. Global OpenSpec feature-flag state

- [x] 1.1 Remove deprecated OpenSpec fields from `Project`; define OpenSpec-domain parsing and serialisation for the structured global `openspec-state` feature flag; verify default, valid, and invalid structured values.
- [x] 1.2 Register `openspec-state` as a global-only structured feature flag and `openspec` as a project-only enablement flag; use the existing global feature-flag get/set API to persist complete state values; verify scope enforcement and configuration round trips.
- [x] 1.3 Remove legacy per-project OpenSpec fields on save without migrating their values; verify an enabled project then starts its OpenSpec task and obtains fresh global state through normal checks.

## 2. OpenSpec consumers

- [x] 2.1 Refactor OpenSpec task and template-context consumers to read structured global `openspec-state` through the existing feature-flag service while preserving `project_flags.openspec` as the per-project enablement gate; verify enabled and disabled project tests pass with the new state source.
- [x] 2.2 Implement the rolling 24-hour version-check guard using decimal UTC Unix timestamp strings, recording both successful and invalid responses through the global feature-flag set API; when an OpenSpec-enabled Project finds absent global state, initialise availability, version, and `checked`; verify task tests cover absent, expired, recent, valid, invalid, enabled, and disabled project cases.
- [x] 2.4 Integrate OpenSpec task start and stop with the existing configuration-change publication and project-task restart lifecycle; verify enabling the current project's flag starts the task and queues an availability check only when state is absent or expired, a successful response queues the version check, disabling it stops the task, and a global state write does not queue duplicate checks.
- [x] 2.3 Update project command templates to render global OpenSpec validation and version information; verify rendered-template tests demonstrate that a project switch retains the same CLI state.

## 3. Complete project cloning

- [x] 3.1 Extend `clone_project` to preserve destination identity while copying project flags, permission paths, additional read paths, and exports; verify clone integration tests retain every transferable source setting, including the per-project OpenSpec enablement flag.
- [x] 3.2 Implement and test documented merge and replacement semantics, including source-wins mapping conflicts and source replacement of permission/read-path lists.
