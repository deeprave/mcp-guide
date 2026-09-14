## 1. Typed document properties and contributor metadata

- [x] 1.1 Trace document collection, ordinary `includes`, `policies:`, missing-policy fallback, status, and command rendering; define one `DocumentContribution` representation that retains rendered content, required frontmatter, and `DocumentProperties` without affecting unrendered partials.
- [x] 1.2 Implement `DocumentProperties` as the central frontmatter dispatcher with typed `DocumentProperty` handlers. Implement `DocumentCache` and `DocumentDisposition`, including defaults and existing domain precedence; verify handlers may consume multiple and overlapping frontmatter keys.
- [x] 1.3 Route both multi-document delivery and partial composition through `DocumentProperties`; inject the exact existing caller-context defaults and conditions, and remove the parallel cache-policy and disposition aggregation paths without changing their established semantics.
- [x] 1.4 Extend policy pre-rendering and Mustache partial registration to retain contributor metadata until accessed-partial tracking is complete; verify a multi-document policy topic preserves each contributor's properties.

## 2. Disposition resolution

- [x] 2.1 Resolve rendered disposition from parent and actually rendered ordinary partial contributors using the established precedence rules; verify a higher-precedence partial changes the parent result and an unused partial does not.
- [x] 2.2 Apply the same resolution to pre-rendered policy contributors; verify a referenced policy partial changes final disposition while an unreferenced topic does not.
- [x] 2.3 Update all content, prompt, command, and status result paths to consume the resolved rendered disposition; verify an end-to-end status or command response preserves `agent/instruction` from a contributing partial.

## 3. Regression coverage and verification

- [x] 3.1 Add behavioural tests for multi-document delivery, direct partials, conditional/skipped partials, single and multiple policy-topic contributors, and downstream disposition delivery; verify cache and disposition preserve their existing independent rules while sharing contributor selection.
- [x] 3.2 Run the focused rendering, content, prompt, command, and status pytest suites in a foreground terminal, then run `ruff check .`, `ruff format --check .`, and `openspec validate fix-partial-disposition --strict --no-interactive`; verify all commands pass.
