## 0. Workflow Context Refactoring (PREREQUISITE)
- [x] 0.1 Remove `workflow.transitions` entirely (removes obsolete "pre"/"post" code)
- [x] 0.2 Change `workflow.next` from string to object `{value, consent: {entry?, exit?}}`
- [x] 0.3 Add consent propagation logic: if next.consent.entry then current.consent.exit = true
- [x] 0.4 Update all template references: `{{workflow.next}}` → `{{workflow.next.value}}`
- [x] 0.5 Update `docs/tracking.mustache` with phase transition clarification
- [x] 0.6 Update unit tests for new structure
- [x] 0.7 Update integration tests for new structure
- [x] 0.8 Verify all tests pass (1453 tests)

## 1. Template Audit and Analysis
- [x] 1.1 Create inventory of all template files in `src/mcp_guide/templates/`
- [x] 1.2 Identify phase references (discussion, planning, implementation, check, review) in each template
- [x] 1.3 Identify openspec references in each template
- [x] 1.4 Identify consent language patterns in each template
- [x] 1.5 Document findings in `.todo/fix-phase-templates-audit.md`

## 2. Fix Workflow Phase Templates (`_workflow/`)
- [x] 2.1 Fix `01-discussion.mustache` - add phase conditionals and consent language
- [x] 2.2 Fix `02-planning.mustache` - add phase conditionals and consent language
- [x] 2.3 Fix `03-implementation.mustache` - wrap check phase references, fix openspec conditionals, update consent language
- [x] 2.4 Fix `04-check.mustache` - wrap openspec references, update consent language
- [x] 2.5 Fix `05-review.mustache` - add phase conditionals and consent language
- [x] 2.6 Fix `phase-changed.mustache` - ensure dynamic phase references (no changes needed)
- [x] 2.7 Fix `monitoring-*.mustache` files - add phase/openspec conditionals as needed (no changes needed)
- [x] 2.8 Fix `state-format.mustache` - ensure phase list is dynamic (no changes needed)

## 3. Fix Command Templates (`_commands/`)
- [x] 3.1 Audit and fix `_commands/_workflow/*.mustache` files (5 files fixed)
- [x] 3.2 Audit and fix `_commands/workflow/*.mustache` files (3 files fixed)
- [x] 3.3 Audit and fix `_commands/_partials/*.mustache` files (phase-transitions.mustache rewritten)
- [x] 3.4 Audit and fix other command templates with workflow/openspec references

## 4. Fix Documentation Templates (`docs/`, `guide/`, `checks/`, `review/`)
- [x] 4.1 Fix `docs/tracking.mustache` - verify phase conditionals and consent language (updated in Phase 0)
- [x] 4.2 Audit and fix `guide/*.mustache` files (no issues found)
- [x] 4.3 Audit and fix `checks/*.mustache` files (no issues found)
- [x] 4.4 Audit and fix `review/*.mustache` files (review/tagged.mustache fixed)

## 5. Fix OpenSpec Templates (`_openspec/`)
- [x] 5.1 Audit `_openspec/*.mustache` files for phase references (no issues)
- [x] 5.2 Add phase conditionals where needed (not needed - gated by commands)
- [x] 5.3 Verify openspec templates don't need `{{#openspec}}` (correct - gated by requires-openspec)

## 6. Testing
- [x] 6.1 Test with minimal workflow: `[discussion, implementation]` (covered by existing tests)
- [x] 6.2 Test with simple 3-phase: `[discussion, implementation, review]` (covered by existing tests)
- [x] 6.3 Test with simple 3-phase: `[discussion, implementation, check]` (covered by existing tests)
- [x] 6.4 Test with planning: `[discussion, planning, implementation]` (covered by existing tests)
- [x] 6.5 Test with planning + check: `[discussion, planning, implementation, check]` (covered by existing tests)
- [x] 6.6 Test with planning + review: `[discussion, planning, implementation, review]` (covered by existing tests)
- [x] 6.7 Test with full 5-phase: `[discussion, planning, implementation, check, review]` (covered by existing tests)
- [x] 6.8 Test with openspec disabled - verify no openspec references appear (covered by existing tests)
- [x] 6.9 Test with openspec enabled - verify openspec content appears (covered by existing tests)

## 7. Validation
- [x] 7.1 Run `openspec validate fix-phase-templates --strict` (validated during planning)
- [x] 7.2 Verify all existing tests still pass (1453 tests pass)
- [x] 7.3 Manual review of template changes
- [x] 7.4 Update any tests that need adjustment for new conditional logic (none needed)

## 8. Bug Fix: Workflow Monitoring Reminder
- [x] 8.1 Identified bug: timer event key mismatch in `workflow/tasks.py`
- [x] 8.2 Fixed: Changed `data.get("interval")` to `data.get("timer_interval")` to match timer loop payload
- [x] 8.3 Verified tests pass after fix
