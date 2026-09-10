## 1. Cache-policy model and frontmatter resolution

- [x] 1.1 Add an immutable cache-policy model and parser for `cache: <lifetime>[, <scope>]`, supporting `long` (24 hours), `medium` (15 minutes), `short` (2 minutes), `public`, `private`, `shared` (an alias for public), `none`, and `no-cache`; default omitted scope to public, omitted lifetime to medium, ordinary non-template Markdown without `cache` to long/public, and invalid declarations to no-cache. Verify focused frontmatter tests cover valid and invalid declarations.
- [x] 1.2 Give CachePolicy readable comparison/equality semantics by restrictiveness and carry declared policy through rendered content; resolve composed documents and partials conservatively.  Verify templates, shortest TTL, private precedence, and an undeclared partial.
- [x] 1.3 Surface invalid cache declarations as content-author diagnostics without making content cacheable; verify a malformed declaration remains deliverable with no policy.
- [x] 1.4 Audit every bundled template under `src/mcp_guide/templates`; add explicit cache frontmatter to each cacheable non-command document, classify flag/settings-dependent or `requires-*` documents as private, and leave command templates no-cache.  Record the audit classification in focused tests or a maintained manifest.

## 2. Content delivery and response metadata

- [x] 2.1 Attach the resolved policy to `get_content`, `read_resource`, and native `guide://` successful content results using `_meta["mcp-guide"]["cache"]`; verify tool and resource integration tests inspect the exact metadata.
- [x] 2.2 Add cache-policy input to response adaptation without generic inference or restoring `io.modelcontextprotocol/cache-*` output, while preserving unrelated result metadata; verify adapter tests for tool, prompt, and resource responses.
- [x] 2.3 Restrict cache-policy propagation to `get_content`, category-content retrieval, and non-command `guide://` delivery; verify prompts, command URIs, and non-document tools remain no-cache.
- [x] 2.4 Isolate any future FastMCP native resource-cache mapping behind a public-API capability check and retain Guide metadata when unsupported; verify the installed FastMCP API path does not use private SDK models.

## 3. Documentation and verification

- [x] 3.1 Document the `cache` frontmatter syntax, no-cache default, composition rules, template behaviour, and Guide metadata contract; verify the documentation renders with `mkdocs build --strict`.
- [x] 3.2 Document that this adds explicit cache policies without restoring formerly removed undocumented protocol-looking cache keys; verify the documentation distinguishes the new contract from historical output.
- [x] 3.3 Run focused frontmatter, content-tool, resource-handler, and response-adapter pytest suites in a foreground PTY, then run `ruff check .` and `openspec validate add-cache-settings --strict --no-interactive`; verify all commands pass.

## 4. MIME part cache headers

- [x] 4.1 Add standard `Cache-Control` headers to single-part and multipart MIME document output using each file's resolved policy; emit `no-cache` for undeclared files and verify mixed-policy multipart content.
