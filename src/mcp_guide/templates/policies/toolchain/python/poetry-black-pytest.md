---
type: agent/instruction
description: >
  Toolchain Policy: poetry + black + pytest (Python). Traditional Python stack: poetry for packaging, black for formatting, pytest for testing.
---
# Toolchain Policy: poetry + black + pytest (Python)

Traditional Python stack: poetry for packaging, black for formatting, pytest for testing.

## Tools

| Role | Tool |
|---|---|
| Package manager | `poetry` |
| Formatter | `black` |
| Linter | `flake8` or `pylint` |
| Type checker | `mypy` |
| Test runner | `pytest` |
| Build backend | `poetry-core` |

## Key commands

```bash
poetry add --group dev pytest pytest-cov black flake8 mypy
poetry run pytest
poetry run black src tests
poetry run flake8 src tests
poetry run mypy src
```

## Rationale

Familiar stack for teams with existing poetry-based projects. Well-established
tooling with broad ecosystem support.
