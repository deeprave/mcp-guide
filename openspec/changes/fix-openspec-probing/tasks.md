# Tasks

## 1. Quiet steady-state OpenSpec lifecycle

- [x] 1.1 Refactor OpenSpec task initialisation and version-refresh handling so disabled projects deactivate, current global state produces no client request, and absent or expired state requests only `openspec --version`; preserve validated, version, and timestamp persistence, and update existing behavioural coverage where required.

## 2. Explicit enable-transition validation

- [x] 2.1 Carry false-to-true OpenSpec flag transition intent through the existing configuration-update queue into the replacement project task; on that transition, inspect `openspec/config.yaml`, direct the user to `guide://_openspec/init` when it is absent, and request the version refresh regardless; update existing behavioural coverage where required.
