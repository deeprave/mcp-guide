---
type: agent/instruction
description: >
  Review Policy: Focused. Review correctness and security. Skip methodology and style compliance.
---
# Review Policy: Focused

Review correctness and security. Skip methodology and style compliance.

## Scope

- Correctness — does the code do what it is supposed to do?
- Security — input validation, injection risks, exposed secrets
- Obvious duplication or re-implementation of existing code

## Out of scope

- YAGNI / SOLID / methodology compliance
- Style preferences
- Consistency with distant parts of the codebase

## Rules

- Cease immediately and report if basic checks fail
- Be specific: cite files and lines, explain impact

## Rationale

Suitable for routine changes where the author is trusted to follow project
conventions and a fast correctness-and-security pass is sufficient.
