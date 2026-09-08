## Context

See [proposal.md](proposal.md) for the motivation.  Earlier Guide cache hints and their `ResponseMetadata` model were removed by a separate change; the current FastMCP response adapter has no cache-policy input or output.  This change adds an explicit policy path without restoring the former undocumented `io.modelcontextprotocol/cache-*` fields.  The installed FastMCP `ResourceResult` public constructor exposes `contents` and `meta`, but no native cache lifetime or scope fields.

Hosted content already retains document frontmatter through rendering, including partial frontmatter.  `get_content`, `read_resource`, and native `guide://` resources converge on that rendering path, while other tools return `Result` values through the common adapter.

## Goals / Non-Goals

**Goals:**

- Make cacheability explicit, safe by default, and author-overridable for hosted documents.
- Preserve an explicit declaration across rendering, partial composition, and every content delivery surface.
- Preserve the removal of undocumented protocol-looking cache hints.
- Make non-document cacheability an explicit producer decision.

**Non-Goals:**

- Inferring cacheability from template syntax, JSON shape, tool name, or apparent determinism.
- Promising client-side caching for MCP result types that do not define a standard cache contract.
- Adding a server-side content cache or changing existing file/OpenSpec caches.
- Automatically modifying existing hosted documents to opt in to caching.

## Decisions

### Use one concise `cache` frontmatter declaration

Hosted documents opt in with:

```yaml
cache: medium, private
```

The comma-separated declaration accepts one lifetime token (`long`, `medium`, or `short`) and one optional scope token (`public` or `private`) in either order. `shared` is accepted as an alias for `public`. `long` is 24 hours, `medium` is 15 minutes, and `short` is 2 minutes. An omitted scope defaults to `public`; an omitted lifetime defaults to `medium`, so `cache: public` and `cache: shared` both mean `medium, public`. `cache: none` and `cache: no-cache` resolve to no-cache. Ordinary non-template Markdown with no `cache` key resolves to `long, public`; other omitted declarations resolve to no-cache. Malformed, duplicate, or unsupported tokens resolve to no-cache with an author diagnostic.

Alternative considered: a mapping with raw milliseconds.  It is needlessly verbose in a document frontmatter block and obscures the intended caching class.

### Default public scope only for genuinely static output

The normal document rendering path does not itself make content private: bundled Markdown is often rendered as a template without consuming dynamic context.  A cacheable declaration with no scope is therefore public by default.  During the bundled-template audit, documents that use `requires-*` directives, flags, settings, or conditional rendering based on those inputs SHALL be classified private and given a medium or short lifetime.  Command templates and command-backed prompt or `guide://_...` output remain no-cache by default.

Alternative considered: make every rendered template private.  That would deny sharing for the predominantly static bundled document set solely because it uses the common rendering path.

### Treat declarations as the authority, resolve conservatively

The rendering layer will produce a small immutable cache-policy value alongside rendered content.  A document's own declaration and every contributing partial's declaration participate in the resolved delivery policy.  No-cache dominates; otherwise the minimum TTL and most restrictive scope (`private` before `public`) win.  The value SHALL provide readable comparison and equality operations using this restrictiveness ordering, so composition can select the safe policy directly.  Template substitution itself is not a disqualifier: an author can declare a policy for a templated result, while an omitted declaration remains no-cache.

Alternative considered: disable cache whenever templates or partials are present.  That rejects safe templated content and is precisely the general guess this change avoids.

### Carry resolved policy explicitly, not as a generic adapter default

Introduce a cache-policy value that content handlers and explicitly opted-in deterministic tool handlers can attach to their `Result`.  The generic response adapter only serialises a policy already resolved by the producer; it never decides that a response is cacheable.

The portable Guide metadata representation will be a namespaced `_meta["mcp-guide"]["cache"]` object containing `ttl_ms` and `scope`.  It describes the declaration to Guide-aware consumers; it is not an MCP cache command.  The adapter will not emit the previously removed `io.modelcontextprotocol/cache-ttl-ms` or `io.modelcontextprotocol/cache-scope` fields on any result type.

Alternative considered: restore the former protocol-looking `_meta` keys.  They are not a documented MCP cache mechanism and conflate adapter transport with a content decision.

### Keep protocol-native cache support isolated behind FastMCP capability

Native `guide://` resource delivery will receive the same resolved Guide policy.  If a future installed FastMCP public API exposes the MCP protocol's native cache fields, a narrow capability adapter can map the resolved policy there as well.  The current implementation will not introspect or construct private SDK models to simulate that API; it will expose the Guide metadata contract only.

Alternative considered: depend on FastMCP internals now.  That would make caching behaviour version-fragile and contradicts the existing public-API migration boundary.

### Limit this change's cache producers to document delivery

The cache-policy carrier and response adapter accept an explicitly resolved policy from any response producer. This change only attaches a policy from document-delivery operations (`get_content`, category-content retrieval, and non-command `guide://` resources); commands, prompts, command URIs, and non-document tools remain no-cache unless a later change explicitly opts them in. The presence of structured content alone has no effect.

Alternative considered: opt in deterministic non-document tools now. Their dynamic data and command semantics make a document-only producer scope clearer and safer for this change, while preserving the adapter capability for a later explicit opt-in.

## Risks / Trade-offs

- [An undeclared rendered partial disables caching for an otherwise cacheable document] → This is deliberately conservative; authors can declare an explicit policy on every contributing document. Ordinary non-template Markdown remains an explicit long/public contributor by default.
- [Guide metadata does not make generic MCP clients cache tool results] → The metadata is honest about the policy.  Protocol-native caching is limited to future public FastMCP support.
- [A client expects the formerly undocumented keys] → Do not restore them; document the new explicit Guide cache-policy contract without implying a migration from currently emitted metadata.
- [Invalid author settings can be missed] → Surface validation diagnostics and resolve invalid settings to no-cache.

## Migration Plan

1. Audit every bundled template and classify non-command documents as static/public, context-dependent/private, or no-cache.
2. Add cache-policy parsing, resolution, focused unit tests, and explicit declarations for the audited cacheable documents.
3. Serialise `mcp-guide.cache` only for resolved policies, without generic adapter inference or legacy cache fields.
4. Document the new frontmatter and metadata contract.
5. Roll back by removing the new cache-policy producer wiring; no persisted cache state or document migration is required.
