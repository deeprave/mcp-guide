## Why

Guide currently emits guessed cache hints through non-standard `_meta` fields on every adapted response.  That neither identifies which content is safe to cache nor lets hosted-document authors override the decision, despite some rendered content and deterministic responses being cacheable.

## What Changes

- Remove the generic, non-standard `io.modelcontextprotocol/cache-*` `_meta` fields from response adaptation.
- Add an explicit `cache` frontmatter setting for hosted documents, with a safe no-cache default and validated scope and lifetime when authors opt in.
- Resolve one cache policy for each delivered content result, including composed and templated content, using the declared policy rather than heuristics about templating or response type.
- Expose the resolved policy in Guide-namespaced result metadata; map it to the MCP protocol's native cache fields for resource responses when the installed FastMCP public API supports them.
- Require non-document tools that opt in to caching to declare their policy explicitly, rather than inheriting a global adapter guess.

## Capabilities

### New Capabilities
- `content-cache-settings`: Explicit cache-policy declaration, validation, and resolution for hosted content and explicitly opted-in tool responses.

### Modified Capabilities
- `frontmatter-processing`: Parse and preserve the cache setting separately from delivered document content.
- `mcp-resources-guide-scheme`: Deliver resolved content cache policy through native `guide://` resource responses.
- `tool-infrastructure`: Attach only explicitly resolved Guide cache policy metadata to eligible tool results and remove generic cache-hint injection.

## Impact

- Affects frontmatter parsing and rendered-content composition, `Result`/response metadata, `get_content`, `read_resource`, native `guide://` resources, and FastMCP response adaptation.
- Changes the external cache metadata contract: the existing undocumented `io.modelcontextprotocol/cache-ttl-ms` and `io.modelcontextprotocol/cache-scope` `_meta` entries are removed.  Cache information becomes explicit, namespaced Guide metadata, with native protocol fields used only where supported by the installed SDK.
- Requires focused tests for default-deny behaviour, invalid frontmatter, composition, templated documents, tool opt-in, and resource delivery.
