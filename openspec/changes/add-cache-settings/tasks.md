## 1. Cache-policy model and frontmatter resolution

- [ ] 1.1 Add an immutable cache-policy model and parser for `cache.ttl_ms` and `cache.scope`, with no-cache as the omitted or invalid default; verify focused frontmatter tests cover valid and invalid declarations.
- [ ] 1.2 Carry declared policy through rendered content and resolve composed documents and partials conservatively; verify tests cover templates, shortest TTL, private precedence, and an undeclared partial.
- [ ] 1.3 Surface invalid cache declarations as content-author diagnostics without making content cacheable; verify a malformed declaration remains deliverable with no policy.

## 2. Content delivery and response metadata

- [ ] 2.1 Attach the resolved policy to `get_content`, `read_resource`, and native `guide://` successful content results using `_meta["mcp-guide/cache"]`; verify tool and resource integration tests inspect the exact metadata.
- [ ] 2.2 Remove `cache_ttl_ms` and `cache_scope` from generic response metadata and remove all `io.modelcontextprotocol/cache-*` adapter output while preserving unrelated result metadata; verify adapter tests for tool, prompt, and resource responses.
- [ ] 2.3 Add explicit cache-policy opt-in at result production for each selected deterministic non-document tool, with no adapter inference; verify each selected tool and an unannotated tool independently.
- [ ] 2.4 Isolate any future FastMCP native resource-cache mapping behind a public-API capability check and retain Guide metadata when unsupported; verify the installed FastMCP API path does not use private SDK models.

## 3. Documentation and verification

- [ ] 3.1 Document the `cache` frontmatter syntax, no-cache default, composition rules, template behaviour, and Guide metadata contract; verify the documentation renders with `mkdocs build --strict`.
- [ ] 3.2 Add release notes for removal of the undocumented protocol-looking cache `_meta` keys and migration to `mcp-guide/cache`; verify the changelog entry names both removed keys.
- [ ] 3.3 Run focused frontmatter, content-tool, resource-handler, and response-adapter pytest suites in a foreground PTY, then run `ruff check .` and `openspec validate add-cache-settings --strict --no-interactive`; verify all commands pass.
