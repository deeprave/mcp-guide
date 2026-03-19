# Change: Migrate type checker from mypy to ty

## Why
Astral's ty provides 10-60x faster type checking, zero-config runs via `uvx`, and completes the Astral toolchain (uv + ruff + ty). It checks untyped code by default, catching bugs mypy silently skips. No mypy plugins are used in this project, removing the main migration blocker.

## What Changes
- Replace mypy with ty as the project type checker
- Translate `[tool.mypy]` configuration to `[tool.ty]` in pyproject.toml
- Convert `# type: ignore` comments to ty equivalents where needed
- Fix any annotation issues surfaced by ty's stricter checking
- Remove mypy and type stub packages from dev dependencies
- Replace the mypy pre-commit hook with a local ty hook
- Update CI workflows to use ty
- Update developer documentation and templates

## Impact
- Affected specs: none (tooling-only change)
- Affected code: pyproject.toml, .pre-commit-config.yaml, CI config, inline type comments, templates
- No production code logic changes expected
- Note: no official `astral-sh/ty-pre-commit` repo exists yet (ty is 0.0.x beta); use local hook for now
