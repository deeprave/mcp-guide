## 1. Contributor metadata

- [ ] 1.1 Trace every rendered-partial path, including ordinary `includes`, `policies:`, missing-policy fallback, status, and command rendering; define one contributor representation that retains rendered content and resolved disposition, and verify it does not affect unrendered partials.
- [ ] 1.2 Extend policy pre-rendering and Mustache partial registration to retain contributor metadata until accessed-partial tracking is complete; verify a multi-document policy topic preserves each contributor's disposition.

## 2. Disposition resolution

- [ ] 2.1 Resolve rendered disposition from parent and actually rendered ordinary partial contributors using the established precedence rules; verify a higher-precedence partial changes the parent result and an unused partial does not.
- [ ] 2.2 Apply the same resolution to pre-rendered policy contributors; verify a referenced policy partial changes final disposition while an unreferenced topic does not.
- [ ] 2.3 Update all content, prompt, command, and status result paths to consume the resolved rendered disposition; verify an end-to-end status or command response preserves `agent/instruction` from a contributing partial.

## 3. Regression coverage and verification

- [ ] 3.1 Add behavioural tests for direct partials, conditional/skipped partials, single and multiple policy-topic contributors, and downstream disposition delivery; verify the new tests fail before the implementation and pass afterwards.
- [ ] 3.2 Run the focused rendering, content, prompt, command, and status pytest suites in a foreground terminal, then run `ruff check .`, `ruff format --check .`, and `openspec validate fix-partial-disposition --strict --no-interactive`; verify all commands pass.
