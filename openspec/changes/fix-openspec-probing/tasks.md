# Tasks

## 1. Quiet steady-state OpenSpec lifecycle

- [ ] 1.1 Refactor OpenSpec task initialisation so disabled projects deactivate, current global state produces no client request, and absent or expired state requests only `openspec --version`; verify focused task tests cover all three observable paths.
- [ ] 1.2 Update the version-refresh instruction and response parsing to omit CLI-location and repository-asset requests while preserving validated, version, and timestamp persistence; verify valid, unavailable, and unparseable version responses.

## 2. Explicit enable-transition validation

- [ ] 2.1 Carry false-to-true OpenSpec flag transition intent through the existing configuration-update queue into the replacement project task; verify a fresh session and project binding do not receive that intent.
- [ ] 2.2 On an explicit enable transition, verify `openspec/config.yaml` and `openspec/changes` before requesting the version refresh, retaining global state when either is absent; verify successful and incomplete-asset paths with lifecycle tests.

## 3. Regression coverage

- [ ] 3.1 Add or revise behavioural tests proving reconnects do not probe assets, changes data remains on demand, and a completed transition does not duplicate requests; verify the focused OpenSpec and project-task test modules pass.
