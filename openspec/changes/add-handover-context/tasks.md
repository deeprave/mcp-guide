# Tasks

## 1. Handoff-context resolution

- [x] 1.1 Register `handoff-context` through the established global-and-project feature-flag constant, validator, normaliser, and resolver path; distinguish disabled, default, filename, and relative-path values; reject absolute paths; verify unit tests cover project-over-global precedence, rejected invalid values, and the disabled default.
- [x] 1.2 Resolve enabled targets against `{{paths.documents}}` or the project root and derive format guidance from their extensions; verify tests cover JSON, Markdown, text, and a non-default filename.
- [x] 1.3 Validate the resolved relative target with the existing `ReadWriteSecurityPolicy.validate_write_path` against `allowed_write_paths`; verify disallowed targets produce no eligible handoff request.

## 2. Milestone guidance

- [x] 2.1 Rename `McpUpdateTask` to `StartupTask` and extend it to resolve, render, and queue one handoff-context system template alongside its existing documentation-update check; verify disabled and enabled delivery behaviour without asserting shipped template prose.
- [x] 2.2 Add template branches for the disabled informational message and the format-specific eligible-target request; preserve ordinary manual user-directed handoff behaviour and verify queued response metadata identifies the configured target and format.
- [x] 2.3 Update existing task-manager and autoupdate OpenSpec contracts for the `StartupTask` rename.

## 3. Documentation and validation

- [x] 3.1 Document global and project `handoff-context` configuration values, target resolution, and the disabled default; verify examples match the implemented contract.
- [x] 3.2 Run focused pytest coverage, Ruff and type checks, strict OpenSpec validation for `add-handover-context`, and `git diff --check`; record any full-suite result or environmental blocker.
- [x] 3.3 Add the optional handoff-context selection to guided onboarding, including disabled, default, and validated custom project targets.
