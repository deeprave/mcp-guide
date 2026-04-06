---
type: agent/instruction
description: >
  Methodology Policy: Domain-Driven Design (DDD). The agent structures code around the core domain model and domain language.
---
# Methodology Policy: Domain-Driven Design (DDD)

The agent structures code around the core domain model and domain language.

## Rules

- Use the ubiquitous language of the domain in code, tests, and documentation
- Identify and respect bounded contexts
- Model domain concepts explicitly (entities, value objects, aggregates,
  domain events, repositories)
- Keep domain logic free from infrastructure concerns
- Anti-corruption layers at context boundaries

## Rationale

DDD is valuable for complex domains where the business model drives software
design. Less suited to simple CRUD applications or utility code.
