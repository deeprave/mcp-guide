## 1. Implementation

- [ ] 1.1 Create `src/mcp_guide/scripts/` directory
- [ ] 1.2 Add `__init__.py` to `src/mcp_guide/scripts/`
- [ ] 1.3 Move `src/scripts/mcp_guide_install.py` to `src/mcp_guide/scripts/mcp_guide_install.py`
- [ ] 1.4 Move `src/scripts/guide_agent_install.py` to `src/mcp_guide/scripts/guide_agent_install.py`
- [ ] 1.5 Update `pyproject.toml` console script entry points for `mcp-install` and `guide-agent-install` to use `mcp_guide.scripts`
- [ ] 1.6 Update test imports in `tests/unit/scripts/test_mcp_guide_install.py` to use `mcp_guide.scripts`

## 2. Testing

- [ ] 2.1 Verify `uv run mcp-install --help` works
- [ ] 2.2 Verify `uvx --from mcp-guide mcp-install --help` works
- [ ] 2.3 Verify `uv run guide-agent-install --help` works
- [ ] 2.4 Verify `uvx --from mcp-guide guide-agent-install --help` works
- [ ] 2.5 Verify all script tests pass
- [ ] 2.6 Verify `osvcheck` still works from `src/scripts/` (development only)
