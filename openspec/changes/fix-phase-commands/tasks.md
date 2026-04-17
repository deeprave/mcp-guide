## 1. Audit and classification

- [ ] 1.1 Confirm the intended semantics of `requires-workflow: [phase]` for workflow command templates
- [ ] 1.2 Inventory phase-changing templates under `src/mcp_guide/templates/_commands/workflow/`
- [ ] 1.3 Separate single-phase transition commands from generic workflow helpers and dynamic phase commands
- [ ] 1.4 Document the expected treatment of `reset.mustache` and `phase.mustache`

## 2. Template corrections

- [ ] 2.1 Update `discuss.mustache` to declare `requires-workflow: [discussion]`
- [ ] 2.2 Update `explore.mustache` to declare `requires-workflow: [exploration]`
- [ ] 2.3 Update `plan.mustache` to declare `requires-workflow: [planning]`
- [ ] 2.4 Update `implement.mustache` to declare `requires-workflow: [implementation]`
- [ ] 2.5 Update `check.mustache` to declare `requires-workflow: [check]`
- [ ] 2.6 Update `review.mustache` to declare `requires-workflow: [review]`
- [ ] 2.7 Update `reset.mustache` to declare `requires-workflow: [discussion]` if reset is specified as a discussion transition command
- [ ] 2.8 Resolve `phase.mustache` by either introducing explicit dynamic phase validation support or documenting why it must remain outside the single-phase pattern

## 3. Validation

- [ ] 3.1 Add or update tests covering workflow command frontmatter validation
- [ ] 3.2 Verify that every single-phase transition command under `_commands/workflow/` uses phase-list syntax
- [ ] 3.3 Verify that non-transition workflow helpers are not incorrectly narrowed
- [ ] 3.4 Run `openspec validate fix-phase-commands --strict`
