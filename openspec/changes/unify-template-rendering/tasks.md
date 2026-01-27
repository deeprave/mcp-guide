# Implementation Tasks

## Analysis
- [ ] Audit all template rendering call sites
- [ ] Document current frontmatter handling differences
- [ ] Identify special cases for system templates (commands, workflow, openspec, common)
- [ ] Map current rendering paths and their differences

## Core Unification
- [ ] Create unified template renderer interface
- [ ] Implement consistent frontmatter parsing
- [ ] Handle template type routing (commands, workflow, openspec, common)
- [ ] Apply frontmatter rules uniformly

## Special Template Types
- [ ] Define handling for command templates
- [ ] Define handling for workflow templates
- [ ] Define handling for openspec templates
- [ ] Define handling for common templates

## Refactoring
- [ ] Consolidate duplicate rendering logic
- [ ] Update all call sites to use unified renderer
- [ ] Remove deprecated rendering functions
- [ ] Update template discovery to work with unified system

## Testing
- [ ] Test frontmatter parsing consistency
- [ ] Test each template type renders correctly
- [ ] Test template includes and partials
- [ ] Verify all existing templates still work
