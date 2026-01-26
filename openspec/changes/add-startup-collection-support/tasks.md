# Implementation Tasks

## Core Implementation
- [ ] Add `on_project()` event handler in GuideMCP initialization chain
- [ ] Implement startup collection detection logic
- [ ] Add instruction injection mechanism with highest priority
- [ ] Update instruction queue to support priority insertion
- [ ] Add "SHOULD NEVER BE IGNORED" phrasing to startup instructions

## Template Updates
- [ ] Update workflow message templates with "SHOULD NEVER BE IGNORED" phrasing
- [ ] Identify all workflow-related templates that need updating

## Testing
- [ ] Test project load with "startup" collection present
- [ ] Test project load without "startup" collection
- [ ] Verify instruction priority ordering
- [ ] Verify "SHOULD NEVER BE IGNORED" phrasing appears correctly

## Documentation
- [ ] Document startup collection convention in project.md or relevant docs
