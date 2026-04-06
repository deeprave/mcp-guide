---
type: agent/instruction
description: >
  Toolchain Policy: pip + pytest (Python). Minimal Python stack: standard pip for packaging, pytest for testing.
---
# Toolchain Policy: pip + pytest (Python)

Minimal Python stack: standard pip for packaging, pytest for testing.

## Tools

| Role | Tool |
|---|---|
| Package manager | `pip` + `venv` |
| Formatter | `black` or `autopep8` |
| Linter | `flake8` |
| Type checker | `mypy` (optional) |
| Test runner | `pytest` |
| Build backend | `setuptools` |

## Key commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
black src tests
flake8 src tests
```

## Rationale

Maximum compatibility. Suitable for projects with strict dependency constraints
or where newer tooling is not available.
