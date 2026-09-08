## ADDED Requirements

### Requirement: HTTP Content Byte-Rate Limits

For HTTP and HTTPS transports, the server SHALL enforce positive, server-owned
byte-rate limits of 1 MiB per second for one request and 10 MiB per second shared
across concurrent requests by default. Operators SHALL be able to configure both
limits before startup, but SHALL NOT disable either limit.

The budgets SHALL account for UTF-8 bytes emitted in a content-bearing MCP
response, including response framing and export frontmatter. Stdio SHALL not use
these HTTP byte-rate budgets.

#### Scenario: HTTP request is paced to its byte-rate budget
- **WHEN** an HTTP or HTTPS content response would otherwise emit bytes faster than the configured per-request byte-rate budget
- **THEN** the server paces delivery so the response does not exceed that rate
- **AND** a response that exceeds the separate maximum content size returns `max_size_exceeded`

#### Scenario: Stdio content response is not throughput-limited
- **WHEN** a stdio client receives a content response within the hard content-size limits
- **THEN** the server does not apply HTTP byte-rate accounting to that response

### Requirement: Shared HTTP Content Capacity

The HTTP and HTTPS transports SHALL use one concurrency-safe shared byte-rate
budget for all content-bearing responses served by the process. A request that
cannot reserve its required shared capacity SHALL fail promptly with a retryable
`server_busy` response and SHALL NOT wait indefinitely or displace bytes reserved
for another request.

#### Scenario: Concurrent requests exhaust server capacity
- **WHEN** concurrent HTTP or HTTPS content requests exhaust the configured shared byte-rate budget
- **THEN** a later request receives a retryable `server_busy` response
- **AND** already admitted requests retain their reserved capacity
