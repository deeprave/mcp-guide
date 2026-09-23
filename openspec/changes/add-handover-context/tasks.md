# Tasks

## 1. Handover-context resolution

- [ ] 1.1 Add a shared resolver for the effective `handoff-context` flag that distinguishes disabled, default, filename, and relative-path values; verify unit tests cover project-over-global precedence and the disabled default.
- [ ] 1.2 Resolve enabled targets against `{{paths.documents}}` or the project root and derive format guidance from their extensions; verify tests cover JSON, Markdown, text, and a non-default filename.
- [ ] 1.3 Validate the resolved target against the project root and existing `allowed_write_paths` policy; verify disallowed targets produce no eligible handover request.

## 2. Milestone guidance

- [ ] 2.1 Integrate the shared eligible target into milestone response guidance so it requests a current handover context only when enabled; verify rendered response behaviour for disabled and enabled configurations without asserting shipped template prose.
- [ ] 2.2 Add the format-specific target reference to the delivered agent guidance and preserve ordinary manual user-directed handover behaviour; verify the response metadata and visible request identify the configured target and format.

## 3. Documentation and validation

- [ ] 3.1 Document global and project `handoff-context` configuration values, target resolution, and the disabled default; verify examples match the implemented contract.
- [ ] 3.2 Run focused pytest coverage, Ruff and type checks, strict OpenSpec validation for `add-handover-context`, and `git diff --check`; record any full-suite result or environmental blocker.
