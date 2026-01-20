# Enforce Explicit Permission for Workflow Phase Transitions

**Status**: Proposed
**Priority**: High
**Complexity**: Medium

## Why

Currently, workflow phase transitions lack clear rules for when explicit user consent, request, or confirmation is required. This creates inconsistent behavior where agents may transition phases without proper user approval, potentially leading to premature implementation or review phases.

The workflow system needs standardized permission controls to:
- Ensure user control over critical phase transitions (entering implementation, leaving review)
- Provide clear template variables for agents to understand transition requirements
- Support flexible workflow configurations while maintaining consistent permission semantics

## What Changes

- Add explicit permission markers to workflow phase definitions using "*" syntax:
  - Preceding "*" (e.g., "*implementation") = explicit consent required to ENTER phase
  - Trailing "*" (e.g., "review*") = explicit consent required to LEAVE phase
  - Both "*phase*" = consent required for both entry and exit
- Create workflow.transitions template variable containing permission metadata for each phase
- Support configurable workflow phases while maintaining required phases (discussion, implementation)
- Provide transition guidance text for templates to instruct agents on permission requirements

## Technical Approach

The workflow.transitions template variable will be structured as:
```javascript
workflow.transitions = {
  "discussion": {
    default: true,
    pre: false,
    post: false
  },
  "planning": {
    pre: false,
    post: false
  },
  "implementation": {
    pre: true,
    post: false
  },
  "check": {
    pre: false,
    post: true
  },
  "review": {
    pre: false,
    post: true
  }
}
```

Where:
- `default`: true for the starting phase (discussion)
- `pre`: true if explicit consent required to enter this phase
- `post`: true if explicit consent required to leave this phase

## Success Criteria

- Workflow templates can access permission metadata via workflow.transitions
- Phase transition logic respects explicit permission requirements
- Default workflow maintains current behavior with proper permission controls
- Custom workflow configurations can define their own permission patterns
- Template rendering includes appropriate transition guidance based on permission settings
