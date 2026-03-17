# Change: Migrate type checker from mypy to ty

## Why
Astral's ty provides 10-60x faster type checking, zero-config runs via `uvx`, and completes the Astral toolchain (uv + ruff + ty). It checks untyped code by default, catching bugs mypy silently skips. No mypy plugins are used in this project, removing the main migration blocker.

## What Changes
- Replace mypy with ty as the project type checker
- Translate `[tool.mypy]` configuration to `[tool.ty]` in pyproject.toml
- Update any `# type: ignore` comments to `# ty: ignore` equivalents
- Remove mypy from dev dependencies
- Update CI workflows to use ty
- Update developer documentation and contributing guidelines

## Impact
- Affected specs: none (tooling-only change)
- Affected code: pyproject.toml, CI config, inline type ignore comments
- No production code logic changes expected
