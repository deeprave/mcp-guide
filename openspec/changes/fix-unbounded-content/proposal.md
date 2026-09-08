## Why

Document discovery currently limits individual glob expansion, but document bodies, stored content, templates, partials, rendered expansions, and aggregate tool responses can still consume unbounded memory and bandwidth.  An HTTP client or a document author can therefore cause disproportionate work or prevent other clients from receiving service.

## What Changes

- Add finite, server-configurable defaults for the number of documents and the bytes of content that one content request may read, render, and return.
- Reject filesystem and SQLite document additions or reads that exceed the document-byte limit before loading an unbounded body.
- Add stricter source, partial-input, and rendered-output limits to template processing so Mustache expansion cannot bypass document or response budgets.
- Enforce a combined document-count limit across a resolved content expression, rather than relying solely on the existing per-glob discovery cap.
- Apply HTTP-only byte-rate budgets to each request and to the server as a whole. A request that exceeds its own budget returns a size-limit failure; a request that cannot reserve the shared server budget receives a retryable server-busy response.

## Capabilities

### New Capabilities

- `content-serving-limits`: Defines request-wide document-count and response-byte budgets, limit errors, and the configuration surface for bounded content delivery.

### Modified Capabilities

- `file-discovery`: Bound the number of documents selected by a complete content request across filesystem and stored-document sources.
- `document-store`: Reject document additions and content reads that exceed the configured document-size limit.
- `template-rendering`: Bound template and partial reads, template expansion, and policy-partial rendering.
- `http-transport`: Apply per-request and server-wide HTTP response byte-rate limits with distinct overload responses.

## Impact

- Affected code: document discovery and SQLite loading, content gathering and formatting, template/partial rendering, and the HTTP transport boundary.
- Affected behaviour: oversized documents, templates, partials, rendered content, and aggregate responses become deterministic failures instead of being read or rendered without limit; HTTP callers may receive a size-limit or retryable busy response.
- Configuration: introduces server-owned content and byte-rate limit settings with secure defaults. Stdio retains the hard content limits but does not use HTTP throughput limiting.
