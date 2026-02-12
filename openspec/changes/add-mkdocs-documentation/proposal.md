# Change: Add MkDocs Documentation

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

User documentation in `docs/user/` needs to be published in an accessible format. MkDocs provides a simple way to generate a static documentation site from the existing Markdown files.

## What Changes

- Add `mkdocs` and `mkdocs-material` to `docs` dependency group in `pyproject.toml`
- Create `mkdocs.yml` configuration file
- Create `docs/index.md` as documentation home page
- Add `site/` directory to `.gitignore` (MkDocs build output)

## Impact

- Affected files: `pyproject.toml`, `mkdocs.yml` (new), `docs/index.md` (new), `.gitignore`
- No changes to existing documentation content
- Enables `mkdocs serve` for local preview and `mkdocs build` for deployment
