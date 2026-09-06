## 1. Evidence-based suite audit

- [ ] 1.1 Inventory every test module and map it to its production surface, recording whether each test protects supported observable behaviour; verify the audit accounts for every file under `tests/`.
- [ ] 1.2 Identify and remove redundant or temporary TDD-only tests after proving equivalent behavioural coverage remains; verify each affected production-area suite passes.
- [ ] 1.3 Review all migration and legacy-named tests, removing only those that do not protect a supported compatibility contract. Distinguish obsolete implementation compatibility from supported legacy MCP protocol behaviour; verify retained protocol compatibility through public boundaries.
- [ ] 1.4 Remove tests that assert class, tool, API, function, or constant existence rather than Guide behaviour; verify replacement behavioural coverage where needed.

## 2. Test quality consolidation

- [ ] 2.1 Consolidate same-setup, same-assertion scenarios into parametrised tests with meaningful case IDs; verify individual parameter cases retain diagnostic output.
- [ ] 2.2 Combine same-topic tests into coherent units without merging distinct setup or behaviours; verify test discovery and focused production-area suites pass.
- [ ] 2.3 Replace implementation-detail and internal mock-call assertions with returned payload, persisted state, emitted instruction, or boundary behaviour assertions where lightweight; verify affected behaviour tests pass.
- [ ] 2.4 Remove or justify avoidable mocks, preserving mocks only at external or nondeterministic boundaries; verify no test becomes order-dependent.

## 3. Complete verification

- [ ] 3.1 Run focused tests for every changed production area in a foreground PTY and verify lint, formatting, type checks, and whitespace checks pass.
- [ ] 3.2 Run the complete pytest suite in a persistent foreground PTY, compare collected test count and duration against the baseline, and verify all tests pass.
