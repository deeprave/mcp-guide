## 1. Assessment
- [ ] 1.1 Document current mypy configuration and options
- [ ] 1.2 Run baseline mypy and record error count
- [ ] 1.3 Run `uvx ty check src/` and compare error output
- [ ] 1.4 Identify any `# type: ignore` comments that need translation

## 2. Configuration
- [ ] 2.1 Create `[tool.ty]` section in pyproject.toml mapping mypy options
- [ ] 2.2 Configure `environment.python-version` and `environment.python`
- [ ] 2.3 Set up `src.exclude` patterns matching current mypy excludes
- [ ] 2.4 Configure rules for any needed suppressions

## 3. Code Updates
- [ ] 3.1 Convert `# type: ignore[code]` comments to `# ty: ignore[code]`
- [ ] 3.2 Address new errors surfaced by ty's stricter checking
- [ ] 3.3 Use `ty check --add-ignore` for baseline if needed

## 4. Dependency Changes
- [ ] 4.1 Remove mypy from dev dependencies
- [ ] 4.2 Add ty to dev dependencies (or use uvx)
- [ ] 4.3 Update uv.lock

## 5. CI and Documentation
- [ ] 5.1 Update CI workflow to use ty instead of mypy
- [ ] 5.2 Update contributing/developer documentation
- [ ] 5.3 Verify all CI checks pass
