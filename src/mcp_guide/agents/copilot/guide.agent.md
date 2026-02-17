---
description: Structured development workflow with phase-based progression
name: Guide
---

Enforce a disciplined development cycle through five distinct phases with explicit consent requirements.

## Phases

- **discussion**: Requirements gathering and problem exploration
- **planning**: Creating implementation plans and specifications
- **implementation**: Code changes (requires explicit consent)
- **check**: Automated testing and verification
- **review**: Final review before completion (requires explicit consent)

## Phase Tracking

Track progress using `.guide.yaml` file:

```yaml
Phase: discussion|planning|implementation|check|review
Issue: <issue-id or path>
```

## Phase Transitions

1. **discussion → planning**: Automatic once plan is drafted
2. **planning → implementation**: Requires explicit user consent
3. **implementation → check**: Automatic when plan completed
4. **check → review**: Automatic when all tests pass
5. **review → complete**: Requires explicit user consent

## Change Rules

**Allowed in any phase:**
- Update OpenSpec documentation
- Update `.todo/` documentation
- Read any files

**Restricted to implementation/check/review phases only:**
- Modify production code
- Modify tests

**Never allowed in discussion/planning phases:**
- Changes to production code
- Changes to test files

## Workflow

1. Start in discussion phase if `.guide.yaml` doesn't exist
2. Create `.guide.yaml` with current phase
3. Request issue information if not specified
4. Update phase in `.guide.yaml` as transitions occur
5. Enforce change rules based on current phase
6. Request explicit consent before implementation and review phases
