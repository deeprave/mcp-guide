# Guide Agent

Structured development workflow with phase-based progression.

## Purpose

Enforces a disciplined development cycle through a structured workflow with an additional non-ordered exploration phase:
- **discussion**: Requirements gathering and problem exploration
- **exploration**: Open-ended investigation, requirement discovery, and option analysis
- **planning**: Creating implementation plans and specifications
- **implementation**: Code changes (requires explicit consent)
- **check**: Automated testing and verification
- **review**: Final review before completion (requires explicit consent)

## Key Features

- Tracks progress via `.guide.yaml` file
- Requires explicit consent for implementation and review phases
- Prevents code changes during discussion/planning phases
- Integrates with OpenSpec for specifications

## Phase Tracking

Phases are tracked using the `.guide.yaml` file with format:
```yaml
Phase: discussion|exploration|planning|implementation|check|review
Issue: <issue-id or path>
```

## Phase Transitions

- **exploration**: Available independently of the ordered delivery sequence; leaving it requires explicit consent
- **discussion** → **planning**: Automatic once plan is drafted
- **planning** → **implementation**: Requires explicit consent
- **implementation** → **check**: Automatic when plan completed
- **check** → **review**: Automatic when all tests pass
- **review** → complete: Requires explicit consent

## Change Rules

- Can update OpenSpec and `.todo/` documentation in any phase
- MUST NOT make changes to production code or tests in discussion/planning/exploration phases
- MAY make changes to production code and tests during implementation/check/review phases
