## Context

See [proposal.md](proposal.md) for the motivation.  `ResponseMetadata` currently carries optional cache lifetime and scope values, and the FastMCP response adapter writes them as undocumented `io.modelcontextprotocol/cache-*` `_meta` keys for tool, prompt, and resource responses.  The installed FastMCP `ResourceResult` public constructor exposes `contents` and `meta`, but no native cache lifetime or scope fields.

Hosted content already retains document frontmatter through rendering, including partial frontmatter.  `get_content`, `read_resource`, and native `guide://` resources converge on that rendering path, while other tools return `Result` values through the common adapter.

## Goals / Non-Goals

**Goals:**

- Make cacheability explicit, safe by default, and author-overridable for hosted documents.
- Preserve an explicit declaration across rendering, partial composition, and every content delivery surface.
- Separate Guide cache-policy information from undocumented protocol-looking cache hints.
- Make non-document cacheability an explicit producer decision.

**Non-Goals:**

- Inferring cacheability from template syntax, JSON shape, tool name, or apparent determinism.
- Promising client-side caching for MCP result types that do not define a standard cache contract.
- Adding a server-side content cache or changing existing file/OpenSpec caches.
- Automatically modifying existing hosted documents to opt in to caching.

## Decisions

### Use one explicit `cache` frontmatter mapping

Hosted documents opt in with:

```yaml
cache:
  ttl_ms: 60000
  scope: private
```

`ttl_ms` is a positive integer and `scope` is `private` or `public`.  Omission, malformed values, and unsupported values resolve to no-cache.  This retains a single discoverable frontmatter keyword while allowing both required policy dimensions to be declared.  The millisecond unit matches the existing result metadata convention and avoids implicit unit conversion.

Alternative considered: a Boolean `cache` field with a global default lifetime.  It cannot express a document's intended lifetime, would encourage broad defaults, and leaves public/private sharing ambiguous.

### Treat declarations as the authority, resolve conservatively

The rendering layer will produce a small immutable cache-policy value alongside rendered content.  A document's own declaration and every contributing partial's declaration participate in the resolved delivery policy.  No-cache dominates; otherwise the minimum TTL and most restrictive scope (`private` before `public`) win.  Template substitution itself is not a disqualifier: an author can declare a policy for a templated result, while an omitted declaration remains no-cache.

Alternative considered: disable cache whenever templates or partials are present.  That rejects safe templated content and is precisely the general guess this change avoids.

### Carry resolved policy explicitly, not as a generic adapter default

Introduce a cache-policy value that content handlers and explicitly opted-in deterministic tool handlers can attach to their `Result`.  The generic response adapter only serialises a policy already resolved by the producer; it never decides that a response is cacheable.

The portable Guide metadata representation will be a namespaced `_meta["mcp-guide/cache"]` object containing `ttl_ms` and `scope`.  It describes the declaration to Guide-aware consumers; it is not an MCP cache command.  The adapter will remove the existing `io.modelcontextprotocol/cache-ttl-ms` and `io.modelcontextprotocol/cache-scope` fields from all result types.

Alternative considered: retain the current protocol-looking `_meta` keys.  They are not a documented MCP cache mechanism and conflate adapter transport with a content decision.

### Keep protocol-native cache support isolated behind FastMCP capability

Native `guide://` resource delivery will receive the same resolved Guide policy.  If a future installed FastMCP public API exposes the MCP protocol's native cache fields, a narrow capability adapter can map the resolved policy there as well.  The current implementation will not introspect or construct private SDK models to simulate that API; it will expose the Guide metadata contract only.

Alternative considered: depend on FastMCP internals now.  That would make caching behaviour version-fragile and contradicts the existing public-API migration boundary.

### Make tool opt-in explicit at registration or result production

Non-document tools such as deterministic status or content tools will only advertise a cache policy when their implementation explicitly supplies one.  The implementation will identify each safe candidate during the apply phase and test it independently.  The presence of structured content alone has no effect.

Alternative considered: classify every tool result by type in `mcp_result_adapter`.  This repeats the current over-general behaviour and gives no tool owner a way to override it.

## Risks / Trade-offs

- [An undeclared partial disables caching for an otherwise cacheable document] → This is deliberately conservative; authors can declare an explicit policy on every contributing document.
- [Guide metadata does not make generic MCP clients cache tool results] → The metadata is honest about the policy.  Protocol-native caching is limited to future public FastMCP support.
- [Existing clients read the undocumented keys] → Remove them as an intentional contract correction and document the new Guide-namespaced metadata in release notes.
- [Invalid author settings can be missed] → Surface validation diagnostics and resolve invalid settings to no-cache.

## Migration Plan

1. Add cache-policy parsing, resolution, and focused unit tests with no existing document opt-ins.
2. Pass resolved policies through content and explicitly selected tool producers.
3. Replace adapter-level protocol-looking keys with `mcp-guide/cache` only for resolved policies.
4. Add release documentation describing the removal and the new frontmatter contract.
5. Roll back by removing the new cache-policy producer wiring; no persisted cache state or document migration is required.
