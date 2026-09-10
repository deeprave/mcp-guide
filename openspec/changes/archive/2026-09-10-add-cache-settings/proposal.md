## Why

Guide previously emitted guessed cache hints through non-standard `_meta` fields, but a separate change removed them.  Guide currently has no response cache-policy output.  Hosted-document authors therefore have no explicit way to declare content that is safe to cache, despite some rendered content and deterministic responses being cacheable.

## What Changes

- Add an explicit, concise `cache` frontmatter setting for hosted documents, with a safe no-cache default for rendered and non-Markdown content; ordinary Markdown defaults to a validated long/shared policy because it is delivered verbatim.
- Resolve one cache policy for each delivered content result, including composed and templated content, using the declared policy rather than heuristics about templating or response type.
- Expose the resolved policy in Guide-namespaced result metadata; map it to MCP-native resource cache fields only when a future installed FastMCP public API supports them.
- Keep commands, prompts, command URIs, and non-document tools opted out of cache-policy delivery.
- Audit every bundled template under `src/mcp_guide/templates` and add cache frontmatter to each cacheable non-command document.

## Capabilities

### New Capabilities
- `content-cache-settings`: Explicit cache-policy declaration, validation, and resolution for hosted content and explicitly opted-in tool responses.

### Modified Capabilities
- `frontmatter-processing`: Parse and preserve the cache setting separately from delivered document content.
- `mcp-resources-guide-scheme`: Deliver resolved content cache policy through native `guide://` resource responses.
- `tool-infrastructure`: Attach only explicitly resolved Guide cache policy metadata to eligible tool results and remove generic cache-hint injection.

## Impact

- Affects frontmatter parsing and rendered-content composition, `Result`/response metadata, `get_content`, `read_resource`, native `guide://` resources, and FastMCP response adaptation.
- Adds an explicit cache-policy contract without restoring the previously removed undocumented `io.modelcontextprotocol/cache-*` entries.  Cache information becomes namespaced Guide metadata, with native protocol fields used only where supported by the installed SDK.
- Requires focused tests for default-deny behaviour, symbolic frontmatter, composition, templated documents, bundled-template coverage, and resource delivery.
