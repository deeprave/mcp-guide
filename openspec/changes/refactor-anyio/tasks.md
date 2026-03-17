## 1. Replace aiofiles in production code
- [x] 1.1 Replace `aiofiles` in `core/file_reader.py` with `anyio.Path.read_text()` *(done)*
- [ ] 1.2 Replace `aiofiles` in `render/frontmatter.py` (2 call sites: read text)
- [ ] 1.3 Replace `aiofiles` in `render/partials.py` (1 call site: read text)
- [ ] 1.4 Replace `aiofiles` in `discovery/commands.py` (1 call site: read text)
- [ ] 1.5 Replace `aiofiles` in `discovery/files.py` (`aiofiles.os.stat`, `aiofiles.os.path.exists`)
- [ ] 1.6 Replace `aiofiles` in `installer/integration.py` (1 call site: write text)
- [ ] 1.7 Replace `aiofiles` in `installer/core.py` (11 call sites: read/write text+binary, file copy)
- [ ] 1.8 Replace `aiofiles` in `scripts/mcp_guide_install.py` (3 call sites: read/write text)
- [ ] 1.9 Remove `aiofiles` from dependencies in `pyproject.toml`
- [ ] 1.10 Verify no remaining `aiofiles` imports in `src/`

## 2. Update tests that mock or use aiofiles directly
- [x] 2.1 Update `test_file_reader.py` mock *(done)*
- [x] 2.2 Update `test_command_security.py` mock *(done)*
- [x] 2.3 Update `test_mcp_guide_install.py` usage *(done)*
- [ ] 2.4 Update `test_category_content.py` mock of `frontmatter.aiofiles.open`
- [ ] 2.5 Verify no remaining `aiofiles` imports in `tests/`

## 3. Standardise test markers
- [ ] 3.1 Convert all `@pytest.mark.asyncio` → `@pytest.mark.anyio` (496 markers, 70 files)
- [ ] 3.2 Remove `asyncio_mode = "auto"` from pyproject.toml
- [ ] 3.3 Remove `pytest-asyncio` from dev dependencies in `pyproject.toml`

## 4. Validation
- [ ] 4.1 Run full test suite — all 1670 tests pass
- [ ] 4.2 Run ruff check and mypy — clean
- [ ] 4.3 Verify `aiofiles` and `pytest-asyncio` are not in `uv.lock`
