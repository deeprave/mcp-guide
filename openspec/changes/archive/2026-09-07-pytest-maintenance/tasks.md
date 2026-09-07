## 1. Evidence-based suite audit

- [x] 1.1 Record a full-suite runtime baseline under the same conditions intended for final verification. Inventory every test module and map it to its current production surface; identify repeated expensive setup and execution and account for every file under `tests/`.
- [x] 1.2 Identify and remove redundant or temporary TDD-only tests after proving equivalent behavioural coverage remains; verify each affected production-area suite passes.
- [x] 1.3 Remove application-compatibility and legacy-state tests, explicitly distinguishing these from legacy and compatibility MCP protocol tests, which must remain. Preserve current behavioural coverage where a removed test also exercised it.
- [x] 1.4 Remove tests that assert class, tool, API, function, or constant existence rather than Guide behaviour; verify replacement behavioural coverage where needed.
- [x] 1.5 Remove tests targeting removed features, tools, classes or functions after cross-referencing the current production surface.

## 2. Test quality consolidation

- [x] 2.1 Consolidate same-setup, same-assertion scenarios into parametrised tests with meaningful case IDs; verify individual parameter cases retain diagnostic output.
- [x] 2.2 Fold redundant single-behaviour and TDD-only checks into comprehensive behavioural scenarios, reducing repeated setup and execution while retaining useful failure diagnostics and test independence.
- [x] 2.3 Replace implementation-detail and internal mock-call assertions with returned payload, persisted state, emitted instruction, or boundary behaviour assertions where lightweight; verify affected behaviour tests pass.
- [x] 2.4 Remove or justify avoidable mocks, preserving mocks only at external or nondeterministic boundaries; verify no test becomes order-dependent.

## 3. Complete verification

- [x] 3.1 Run focused tests for every changed production area in a foreground PTY and verify lint, formatting, type checks, and whitespace checks pass.
- [x] 3.2 Run the complete pytest suite in a persistent foreground PTY under baseline-equivalent conditions; verify all tests pass and report the measured runtime reduction. Report collected case count separately; fewer functions or parametrisation alone do not establish a speed improvement.
