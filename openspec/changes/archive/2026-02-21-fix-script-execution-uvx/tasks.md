## 1. Implementation

- [x] 1.1 Create `src/mcp_guide/scripts/` directory
- [x] 1.2 Add `__init__.py` to `src/mcp_guide/scripts/`
- [x] 1.3 Move `src/scripts/mcp_guide_install.py` to `src/mcp_guide/scripts/mcp_guide_install.py`
- [x] 1.4 Move `src/scripts/guide_agent_install.py` to `src/mcp_guide/scripts/guide_agent_install.py`
- [x] 1.5 Update `pyproject.toml` console script entry points for `mcp-install` and `guide-agent-install` to use `mcp_guide.scripts`
- [x] 1.6 Update test imports in `tests/unit/scripts/test_mcp_guide_install.py` to use `mcp_guide.scripts`

## 2. Migrate osvcheck to external package

- [x] 2.1 Remove `osvcheck` entry from `[project.scripts]` in `pyproject.toml`
- [x] 2.2 Delete `src/scripts/osvcheck.py`
- [x] 2.3 Update `.pre-commit-config.yaml` to use external osvcheck repo
- [x] 2.4 Test pre-commit hook with `pre-commit run osvcheck --all-files`

## 3. Testing

- [x] 3.1 Verify `uv run mcp-install --help` works
- [x] 3.2 Verify `uvx --from mcp-guide mcp-install --help` works
- [x] 3.3 Verify `uv run guide-agent-install --help` works
- [x] 3.4 Verify `uvx --from mcp-guide guide-agent-install --help` works
- [x] 3.5 Verify all script tests pass
