# Implementation Tasks: Enhance requires-* Checking

## 1. Design & Planning

- [ ] 1.1 Review current `check_frontmatter_requirements()` implementation
- [ ] 1.2 Design generic checking algorithm for list/dict/boolean requirements
- [ ] 1.3 Design workflow flag structure and validation
- [ ] 1.4 Plan backward compatibility strategy
- [ ] 1.5 Identify all templates using `requires-*` directives

## 2. Core Implementation

- [ ] 2.1 Implement enhanced `check_requires_directive()` function
  - [ ] 2.1.1 Boolean checking (truthy)
  - [ ] 2.1.2 List membership checking
  - [ ] 2.1.3 List containment checking (all items present)
  - [ ] 2.1.4 Key-value pair parsing and checking
  - [ ] 2.1.5 Exact match fallback
- [ ] 2.2 Integrate into `render_template()` replacing simple truthy check
- [ ] 2.3 Add comprehensive unit tests for all checking modes

## 3. Workflow Flag Enhancement

- [ ] 3.1 Update workflow flag type definition
- [ ] 3.2 Implement flag validation to expand `workflow: true`
- [ ] 3.3 Support three formats: list, dict, boolean
- [ ] 3.4 Update workflow flag resolution logic
- [ ] 3.5 Add tests for workflow flag validation

## 4. Template Updates

- [ ] 4.1 Audit workflow command templates for `requires-workflow` usage
- [ ] 4.2 Update templates to use new checking format if needed
- [ ] 4.3 Test workflow commands with new checking logic
- [ ] 4.4 Update documentation for template authors

## 5. Cleanup & Migration

- [ ] 5.1 Identify all uses of `check_frontmatter_requirements()`
- [ ] 5.2 Verify all uses are migrated to new API
- [ ] 5.3 Remove `check_frontmatter_requirements()` function
- [ ] 5.4 Remove related legacy code
- [ ] 5.5 Update imports and references

## 6. Testing & Validation

- [ ] 6.1 Test boolean requirements
- [ ] 6.2 Test list membership requirements
- [ ] 6.3 Test list containment requirements
- [ ] 6.4 Test key-value pair requirements
- [ ] 6.5 Test workflow flag expansion
- [ ] 6.6 Test workflow phase checking
- [ ] 6.7 Test workflow consent checking
- [ ] 6.8 Run full test suite
- [ ] 6.9 Test with real workflow commands

## 7. Documentation

- [ ] 7.1 Document new `requires-*` checking behavior
- [ ] 7.2 Document workflow flag formats
- [ ] 7.3 Update template authoring guide
- [ ] 7.4 Add examples for each checking mode
- [ ] 7.5 Document migration from old to new format
