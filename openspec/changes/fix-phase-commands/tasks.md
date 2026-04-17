## 1. Audit and classification

- [x] 1.1 Confirm the intended semantics of `requires-workflow: [phase]` for workflow command templates
- [x] 1.2 Inventory phase-changing templates under `src/mcp_guide/templates/_commands/workflow/`
- [x] 1.3 Separate optional single-phase transition commands from generic workflow helpers and dynamic phase commands
- [x] 1.4 Document that `discuss`, `implement`, `explore`, `reset`, `issue`, and `show` remain valid on `requires-workflow: true`

## 2. Template corrections

- [x] 2.1 Update `plan.mustache` to declare `requires-workflow: [planning]`
- [x] 2.2 Update `explore.mustache` to declare `requires-workflow: [exploration]` and use exploration-phase instructions
- [x] 2.3 Update `check.mustache` to declare `requires-workflow: [check]`
- [x] 2.4 Update `review.mustache` to declare `requires-workflow: [review]`
- [x] 2.5 Introduce workflow-scoped `contains` and `notcontains` lambdas for dynamic workflow membership checks
- [x] 2.6 Update `phase.mustache` to reject unavailable phases using workflow-scoped membership helpers and `{{#_error}}`

## 3. Validation

- [x] 3.1 Add or update tests proving nested workflow membership lambdas work for configured and missing phases
- [x] 3.2 Add or update tests covering workflow command frontmatter validation
- [x] 3.3 Verify that optional single-phase commands use phase-list syntax and generic workflow helpers are not incorrectly narrowed
- [x] 3.4 Run `openspec validate fix-phase-commands --strict`
