---
type: agent/instruction
description: >
  Review Policy: Minimal. Quick sanity check for obvious bugs and security issues only.
---
# Review Policy: Minimal

Quick sanity check for obvious bugs and security issues only.

## Scope

- Obvious bugs — logic errors, off-by-ones, null dereferences
- Critical security issues — hardcoded secrets, SQL injection, unvalidated input

## Out of scope

- Style, methodology, duplication, complexity
- Anything that is not an obvious defect

## Rationale

Appropriate for low-risk changes, config updates, or documentation where a
full review would add overhead without value.
