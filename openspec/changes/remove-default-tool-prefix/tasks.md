## 1. Implementation
- [x] 1.1 `tool_decorator.py` — change `get_tool_prefix()` env default from `"guide"` to `""`
- [x] 1.2 `cli.py` — change `ServerConfig.tool_prefix` default from `"guide"` to `""`; remove `--no-tool-prefix` flag and its handling; update `--tool-prefix` help text
- [x] 1.3 Update tests — fix CLI tests, integration test tool names, conftest helpers for empty prefix
- [x] 1.4 Run tests (`uv run pytest`) — 1522 passed, 2 pre-existing failures (circular import in test_deferred_registration.py, unrelated)
- [x] 1.5 Run `uv run ruff check src` and `uv run mypy src` — clean
