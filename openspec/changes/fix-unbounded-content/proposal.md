## Why

Content retrieval can select, read, render, and serialise unbounded data. HTTP
requests can also overwhelm one server process before normal MCP handling.

## What Changes

- Add static, global operator configuration for a 500 MB default content limit
  and 100-document request limit.
- Apply those limits before filesystem or stored bodies are materialised, while
  rendering templates and partials, and to final document responses.
- Add HTTP-only inbound request admission: 5 requests/second per established
  session and 100 requests/second per server process, measured over 15 seconds.
- Return HTTP 429 for a session limit and 503 for exhausted service capacity,
  each with a naturally decreasing `Retry-After` value.

## Non-Goals

- No client or project setting, runtime reload, stdio rate limit, or
  multi-process/distributed rate budget.

## Impact

The global configuration, content discovery/rendering/store paths, document
delivery tools, and HTTP transport are affected.
