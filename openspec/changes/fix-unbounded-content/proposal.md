## Why

Content retrieval can select, read, render, and serialise unbounded data. HTTP
requests can also overwhelm one server process before normal MCP handling.

## What Changes

- Add static, global operator configuration for a 500 MB default content limit
  and 100-document request limit.
- Preflight static filesystem and stored-document sources, then apply the
  aggregate content limit to retained non-empty rendered documents; bound each
  template or partial render and final document response.
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
