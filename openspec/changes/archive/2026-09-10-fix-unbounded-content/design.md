## Context

Content documents are sourced from the filesystem and SQLite, then optionally
rendered and serialised. A single request must not cause unbounded source reads,
document selection, rendered output, or final delivery. HTTP requires a separate
inbound admission boundary; stdio does not.

## Decisions

### One immutable global configuration snapshot

`ContentLimits` is loaded from the global configuration at startup and retained
for the process lifetime. The defaults are `max-content-limit: 500mb`,
`max-document-limit: 100`, `http-session-rate-limit: 5`, and
`http-service-rate-limit: 100`. No default values are persisted. Content units
are decimal and accept `B`, `KB`, `MB`, and `GB` case-insensitively.

This is deliberately not a feature flag, project configuration, or client-set
value: it protects the server before a project can safely be selected.

### Retained rendered-content budget with source and response bounds

The configured content limit applies independently to every source
document/template/partial, every rendered template, and the final serialised
document response. Filesystem and SQLite metadata are checked before body reads.
The request's distinct selected documents are counted after aggregation and
de-duplication.

One aggregate UTF-8 byte budget is consumed only after a document has passed
frontmatter requirements, rendered successfully, and produced non-empty content.
Filtered and empty documents do not consume the aggregate budget or count toward
the document limit. Each rendered template and the final serialised response
retain their own content limits; formatters use bounded accumulators so MIME
framing and separators are included before the final response string exists. A
failure is `max_size_exceeded`, does not expose rejected content, and never
returns a partial document response.

### HTTP request admission uses a rolling window

The HTTP ASGI boundary records admitted request timestamps for 15 seconds. It
checks the process budget first, then a known MCP session budget. Before a session
exists, only the process budget applies. A rejected request consumes no capacity.
The oldest admitted timestamp determines `Retry-After`, so retry availability
returns smoothly without a synthetic penalty or backoff.

The FastMCP Streamable HTTP manager is the authority for whether a presented
connection identifier is live. Unknown IDs are treated as pre-session requests
and do not create local session state. Local counter entries are removed once
their rolling window empties.

HTTP returns 429 for a session limit and 503 for process capacity. Each process
maintains its own 100 r/s default budget; deployment-wide limiting belongs at an
upstream proxy. Stdio bypasses this admission layer.

## Risks and mitigations

- Existing oversized SQLite rows remain durable but are rejected before body
  materialisation.
- Source templates, partials, and policy partials receive the active limits and
  are preflighted by byte size. Their independently bounded rendered output is
  included in the retained-content budget only when it is returned to the caller.
- HTTP session identifiers are only used after FastMCP has established them;
  pre-session requests share only the bounded process window.
