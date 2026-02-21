# Change: Refactor osvcheck into separate project

## Why

The `osvcheck` tool is a fully reusable security scanner with no dependencies on mcp-guide. Keeping it in this project forces it to be installed in production environments via `uvx --from mcp-guide`, even though it's only needed for development. Extracting it into a standalone project allows:

- Independent versioning and releases
- Reuse across multiple projects
- Proper documentation and configuration
- Clean separation: mcp-guide users don't get an unnecessary dev tool

## What Changes

- Remove `src/scripts/osvcheck.py` from mcp-guide
- Create new standalone `osvcheck` project with:
  - Proper documentation (README, usage guide)
  - Configuration support (`[tool.osvcheck]` in pyproject.toml)
  - PyPI publication
- Add `osvcheck` as a dev dependency in mcp-guide's `[dependency-groups]`
- Remove `osvcheck` from `[project.scripts]` in mcp-guide

## Impact

- Affected specs: `installation`
- Affected code: `src/scripts/osvcheck.py` (removed), `pyproject.toml` (remove script entry, add dev dependency)
- **BREAKING**: None - osvcheck becomes a separate installable tool
- Users: No impact (osvcheck is dev-only)
- Developers: Install via `uv sync` (automatic with dev dependencies)
