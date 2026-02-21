## 1. Create Standalone osvcheck Project
- [x] 1.1 Create new repository for osvcheck
- [x] 1.2 Copy `src/scripts/osvcheck.py` to new project as main module
- [x] 1.3 Create pyproject.toml with project metadata
- [x] 1.4 Add `[project.scripts]` entry: `osvcheck = "osvcheck:main"`
- [x] 1.5 Add `[tool.osvcheck]` configuration section support
- [x] 1.6 Create README.md with usage documentation
- [x] 1.7 Add LICENSE file
- [x] 1.8 Publish to PyPI

## 2. Update mcp-guide Project
- [x] 2.1 Remove `src/scripts/osvcheck.py`
- [x] 2.2 Remove `osvcheck = "scripts.osvcheck:main"` from `[project.scripts]`
- [x] 2.3 Add `osvcheck` to `[dependency-groups]` dev section
- [x] 2.4 Run `uv sync` to install osvcheck from PyPI
- [x] 2.5 Update any documentation referencing osvcheck location

## 3. Verify
- [x] 3.1 Verify `uv run osvcheck` works in mcp-guide dev environment
- [x] 3.2 Verify osvcheck is NOT in production install (`uvx --from mcp-guide osvcheck` fails)
- [x] 3.3 Verify osvcheck can be installed independently (`uvx osvcheck`)
