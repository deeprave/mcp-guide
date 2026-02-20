## 1. Create Standalone osvcheck Project
- [ ] 1.1 Create new repository for osvcheck
- [ ] 1.2 Copy `src/scripts/osvcheck.py` to new project as main module
- [ ] 1.3 Create pyproject.toml with project metadata
- [ ] 1.4 Add `[project.scripts]` entry: `osvcheck = "osvcheck:main"`
- [ ] 1.5 Add `[tool.osvcheck]` configuration section support
- [ ] 1.6 Create README.md with usage documentation
- [ ] 1.7 Add LICENSE file
- [ ] 1.8 Publish to PyPI

## 2. Update mcp-guide Project
- [ ] 2.1 Remove `src/scripts/osvcheck.py`
- [ ] 2.2 Remove `osvcheck = "scripts.osvcheck:main"` from `[project.scripts]`
- [ ] 2.3 Add `osvcheck` to `[dependency-groups]` dev section
- [ ] 2.4 Run `uv sync` to install osvcheck from PyPI
- [ ] 2.5 Update any documentation referencing osvcheck location

## 3. Verify
- [ ] 3.1 Verify `uv run osvcheck` works in mcp-guide dev environment
- [ ] 3.2 Verify osvcheck is NOT in production install (`uvx --from mcp-guide osvcheck` fails)
- [ ] 3.3 Verify osvcheck can be installed independently (`uvx osvcheck`)
