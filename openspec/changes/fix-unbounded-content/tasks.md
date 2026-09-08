## 1. Limit configuration and shared budget primitives

- [ ] 1.1 Add validated server-owned content-limit and HTTP byte-rate settings with the specified finite defaults, and verify unit tests reject zero, negative, non-integer, and unlimited values at startup.
- [ ] 1.2 Implement immutable `ContentLimits`, request-scoped content accounting, and a safe `max_size_exceeded` result mapping, and verify unit tests identify the exceeded limit without exposing rejected content.

## 2. Bounded document selection and storage

- [ ] 2.1 Add byte-size metadata queries for stored documents and preflight size checks for filesystem discovery, and verify tests obtain both source sizes without loading document bodies.
- [ ] 2.2 Enforce the aggregate distinct-document limit across multi-category and nested-collection expressions, and verify integration tests fail rather than silently truncating the selected set.
- [ ] 2.3 Bound SQLite document add, replace, and read operations before commit or body materialisation, and verify tests preserve an existing row after an oversized replacement and reject legacy oversized rows on read.
- [ ] 2.4 Apply the request response-byte budget to content formatting and export frontmatter, and verify `get_content` and `export_content` return no partial payload when their aggregate response exceeds the limit.

## 3. Bounded template processing

- [ ] 3.1 Route template, frontmatter include, and policy-partial loading through the shared preflight limit checks, and verify tests reject oversized source before parsing or rendering.
- [ ] 3.2 Track partial count and aggregate partial source bytes for each template render, and verify tests cover both ordinary includes and policy partial fan-out.
- [ ] 3.3 Replace unbounded rendered-string collection with a bounded counting output sink that participates in the request budget, and verify a repeating Mustache section aborts before an oversized string is constructed.

## 4. HTTP admission and pacing

- [ ] 4.1 Integrate a concurrency-safe process-wide byte-rate reservation and per-request paced response body with the HTTP and HTTPS response adapter, and verify basic and Streamable HTTP responses account for final encoded bytes.
- [ ] 4.2 Return a retryable `server_busy` response when shared capacity cannot be reserved, release unused reservations on cancellation, and verify concurrent/cancellation integration tests preserve admitted-request capacity.
- [ ] 4.3 Keep stdio outside HTTP byte-rate accounting while retaining all hard content bounds, and verify transport-specific tests cover that distinction.

## 5. Documentation and verification

- [ ] 5.1 Document all limit settings, secure defaults, `max_size_exceeded`, and retryable `server_busy` behaviour for operators and clients, and verify documentation examples match the implemented configuration names.
- [ ] 5.2 Run focused storage, discovery, rendering, content-tool, and HTTP transport tests plus the relevant full test suite, and verify `uv run pytest` completes successfully with no limit-regression failures.
- [ ] 5.3 Validate the completed OpenSpec change against its artefacts with `openspec validate fix-unbounded-content --type change --strict` and verify no validation errors remain.
