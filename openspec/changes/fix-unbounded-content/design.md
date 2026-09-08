## Context

See [proposal.md](proposal.md) for the motivation. Discovery currently retains
filesystem size metadata but reports stored documents with zero size; body loading,
Mustache rendering, and final formatting all produce complete Python strings. The
existing glob limit protects only one glob expansion, not an expression spanning
collections or categories. HTTP responses have no shared byte-capacity control.

The change must protect filesystem and SQLite sources, regular document processing,
templates and their partials, and exported content without weakening the existing
path-security and result contracts. Hard content bounds apply to every transport;
byte-rate controls apply only at the HTTP/HTTPS delivery boundary.

## Goals / Non-Goals

**Goals:**

- Establish a single immutable `ContentLimits` configuration loaded at server start.
- Reject excessive input before a body is read, parse work begins, or a SQLite update
  commits.
- Carry one request budget through discovery, rendering, formatting, and export so
  independently bounded stages cannot combine into an unbounded response.
- Pace admitted HTTP responses per request and preserve process-wide capacity for
  concurrent clients.

**Non-Goals:**

- Changing document formats, Mustache semantics, document-root security, or content
  selection order.
- Applying HTTP throughput controls to stdio.
- Offering user- or project-configurable limits, unlimited modes, queued admission,
  or a distributed rate limiter across processes.

## Decisions

### One server-owned limits object with finite defaults

Create `ContentLimits` from CLI/environment configuration before server startup and
attach the validated object to the runtime. Its defaults are: 100 selected
documents/request, 1 MiB/document, 256 KiB/template or partial source,
32 partials/template, 1 MiB aggregate partial source/template, 1 MiB rendered
template, 4 MiB returned content/request, 1 MiB/s/request, and 10 MiB/s/process.
All values are positive integers; configuration cannot disable a protection.

Server configuration is selected over feature flags or project configuration because
limits protect the server before a request can safely resolve a project. Keeping the
values in one object avoids different code paths using incompatible defaults.

Alternative considered: per-project feature flags. Rejected because a project may
be hostile or absent, and per-project values would make global capacity accounting
ambiguous.

### Preflight source sizes and thread an aggregate request budget

Filesystem discovery will use `stat` size. SQLite metadata/discovery will query the
UTF-8 byte size independently of the `content` value, and stored additions will
measure encoded bytes before opening a write transaction. A `ContentBudget` is
created for each get/export operation; it counts distinct selected documents and
consumes rendered/serialised bytes before they are passed to the result adapter.

Existing rows that predate the limit are checked on read, so an upgrade cannot keep
serving oversized data. Content discovery reports an explicit limit failure instead
of silently truncating a collection.

Alternative considered: only checking `len()` after each existing `read_text()` or
database result. Rejected because it materialises precisely the body the limit is
meant to prevent and cannot constrain aggregate selection before expensive work.

### Make template reads and rendering bounded operations

Template, frontmatter-include, and policy-partial paths will all use the same
preflight size check and a render-scoped partial counter/aggregate source budget.
The renderer will write to a counting, bounded text sink; exceeding the output
budget stops expansion via a dedicated limit signal rather than constructing an
oversized final string and then inspecting it.

The bounded sink is preferred to post-render length checks because Mustache sections
can multiply small input into a large output. The template's rendered bytes are also
charged to the enclosing request budget, so multiple valid templates cannot bypass
the response limit.

Alternative considered: relying only on the 4 MiB response cap. Rejected because it
does not limit a single render's peak allocation, partial fan-out, or work before
formatting.

### Rate-limit HTTP response delivery with admission and pacing

The HTTP transport will use a concurrency-safe process-wide token bucket with a
10 MiB capacity and 10 MiB/s refill rate. Before a content-bearing response begins,
it reserves its known serialised byte count. If the reservation is unavailable,
the transport returns a retryable `server_busy` response immediately; it does not
queue the request. Once admitted, an independent request bucket paces emission at
1 MiB/s. The HTTP response body is emitted in counted chunks so response framing and
payload bytes are measured at the actual transport boundary.

This splits overload admission (`server_busy`) from content validity
(`max_size_exceeded`): a valid response can be paced, while an oversized response
never enters delivery. A single process-wide limiter is adequate for the current
server model and prevents a client identity bypass.

Alternative considered: per-client rate limits. Rejected because client identity is
not trustworthy or consistently available before authentication, and it would not
protect the server's aggregate egress capacity. Alternative considered: sleeping
until global capacity is available. Rejected because it creates unbounded request
queues under load.

## Risks / Trade-offs

- [A legitimate document or template exceeds a default limit] → Operators can raise
  a finite server setting deliberately; errors name the limit and safe remediation.
- [Exact HTTP framing size differs across protocol modes] → Count the final UTF-8
  body/framing at the common HTTP response adapter and cover both basic and
  Streamable HTTP integration tests.
- [A rendering library cannot write directly to a bounded sink] → Introduce a small
  adapter that exposes its supported output interface and aborts on the limit; do
  not fall back to post-render-only checking.
- [Existing SQLite databases contain oversized rows] → Preserve rows on migration
  but reject their body reads and surface a deterministic size error.
- [Token-bucket reservation overestimates work after a disconnect] → Release unused
  reserved capacity on cancellation and test cancellation/concurrent admission.

## Migration Plan

1. Add configuration parsing and validation, content budget primitives, and tests
   without changing default limits.
2. Apply preflight bounds to SQLite add/read and filesystem/stored discovery, then
   enforce the aggregate content result budget.
3. Route all template and partial reads through bounded loading and replace
   unbounded render collection with the bounded sink.
4. Add HTTP response admission/pacing for both HTTP modes, including cancellation
   cleanup and retryable busy responses.
5. Release with documented defaults and limit errors. Roll back by deploying the
   prior server version; no schema migration or content rewrite is required.
