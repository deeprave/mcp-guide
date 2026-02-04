# Implementation Tasks: Enhance requires-* Checking

## 1. Design & Planning

- [x] 1.1 Review current `check_frontmatter_requirements()` implementation
- [x] 1.2 Design generic checking algorithm for list/dict/boolean requirements
- [x] 1.3 Design workflow flag structure and validation
- [x] 1.4 Plan backward compatibility strategy (not needed - unreleased product)
- [x] 1.5 Identify all templates using `requires-*` directives

## 2. Core Implementation

- [x] 2.1 Implement enhanced `_check_requires_directive()` function
  - [x] 2.1.1 Boolean checking (truthy)
  - [x] 2.1.2 List membership checking (ANY match - OR logic)
  - [x] 2.1.3 Exact match fallback
- [x] 2.2 Integrate into `render_template()` replacing simple truthy check
- [x] 2.3 Add comprehensive unit tests for all checking modes

## 3. Workflow Flag Enhancement

- [x] 3.1 Remove marker functions from workflow constants
- [x] 3.2 Add DEFAULT_WORKFLOW_CONSENT constant
- [x] 3.3 Add FLAG_WORKFLOW_CONSENT constant
- [x] 3.4 Implement workflow-consent flag validator
- [x] 3.5 Update workflow context building to use both flags
- [x] 3.6 Remove extract_phase_name() function
- [x] 3.7 Update parse_workflow_phases() to not use markers
- [x] 3.8 Add tests for workflow flag validation

## 4. Template Updates

- [x] 4.1 Audit workflow command templates for `requires-workflow` usage (all use simple boolean check)
- [x] 4.2 Templates work with new checking logic (no changes needed)

## 5. Cleanup & Migration

- [x] 5.1 Identify all uses of `check_frontmatter_requirements()` (3 locations)
- [x] 5.2 Update `check_frontmatter_requirements()` to use enhanced checking
- [x] 5.3 Share `_check_requires_directive()` between template.py and frontmatter.py
- [x] 5.4 Update all workflow transition tests
- [x] 5.5 Update workflow flag tests
- [x] 5.6 Update workflow integration tests

## 6. Testing & Validation

- [x] 6.1 Test boolean requirements
- [x] 6.2 Test list membership requirements (scalar, list, dict)
- [x] 6.3 Test workflow flag expansion (true → default phases)
- [x] 6.4 Test workflow consent expansion (true/false/custom)
- [x] 6.5 Test workflow phase checking
- [x] 6.6 Test workflow consent checking
- [x] 6.7 Run full test suite (1297 tests passed)
- [x] 6.8 Type checking passed
- [x] 6.9 Linting passed
- [x] 6.10 Formatting passed

## 7. Documentation

- [x] 7.1 Document new `requires-*` checking behavior (in spec)
- [x] 7.2 Document workflow flag formats (in spec)
- [x] 7.3 Update template authoring guide (deferred to add-user-documentation)
- [x] 7.4 Add examples for each checking mode (in spec)
- [x] 7.5 Document migration from old to new format (not needed - unreleased)
