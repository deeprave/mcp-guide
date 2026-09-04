## 1. Dependency and transport migration

- [ ] 1.1 Replace the optional Uvicorn dependency with Hypercorn and regenerate the lock file; verify `uv sync --extra http` installs the HTTP transport dependencies.
- [ ] 1.2 Refactor `HttpTransport` to serve FastMCP's ASGI application through Hypercorn's asynchronous API with explicit shutdown; verify focused transport lifecycle tests pass.
- [ ] 1.3 Preserve host, port, TLS certificate, TLS key, endpoint-path, logging, startup-error, and awaited-shutdown behaviour; verify focused unit tests cover each configuration path.

## 2. HTTP compatibility and documentation

- [ ] 2.1 Add integration coverage that confirms the configured MCP endpoint remains reachable over HTTP/1.1 and keeps FastMCP-owned Streamable HTTP handling; verify the integration tests pass.
- [ ] 2.2 Add HTTP/2-capable configuration coverage without depending on external network infrastructure; verify the selected Hypercorn configuration enables HTTP/2 negotiation for TLS deployments.
- [ ] 2.3 Update user installation and deployment documentation to describe direct HTTP/2 capability, HTTP/1.1 fallback, TLS requirements, and reverse-proxy compatibility; verify `mkdocs build --strict` passes.

## 3. Verification

- [ ] 3.1 Run `uv run ruff format --check`, `uv run ruff check --no-cache`, and `uv run ty check`; resolve all findings.
- [ ] 3.2 Run `uv run pytest -Walways -Werror -q` in a foreground PTY and verify the complete suite passes without warnings or hangs.
- [ ] 3.3 Run `openspec validate migrate-hypercorn-asgi --strict --no-interactive` and `git diff --check`; verify both pass.
