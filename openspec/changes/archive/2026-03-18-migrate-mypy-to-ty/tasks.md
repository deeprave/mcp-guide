## 1. Assessment
- [x] 1.1 Run baseline mypy and record current error count
- [x] 1.2 Run `uvx ty check src/` and capture output
- [x] 1.3 Identify `# type: ignore` comments that need translation

## 2. Configuration
- [x] 2.1 Add `[tool.ty]` section in pyproject.toml
- [x] 2.2 Remove `[tool.mypy]` section and overrides from pyproject.toml

## 3. Code Updates
- [x] 3.1 Convert `# type: ignore` comments to ty equivalents
- [x] 3.2 Fix annotation issues surfaced by ty

## 4. Dependency Changes
- [x] 4.1 Remove mypy and type stub packages from dev dependencies
- [x] 4.2 Update uv.lock

## 5. Pre-commit
- [x] 5.1 Replace mypy-check hook with local ty hook in .pre-commit-config.yaml

## 6. CI and Documentation
- [x] 6.1 Update CI workflow to use ty instead of mypy
- [x] 6.2 Update templates referencing mypy
