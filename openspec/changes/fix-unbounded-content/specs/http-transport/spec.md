## ADDED Requirements

### Requirement: HTTP inbound request admission

HTTP and HTTPS SHALL admit at most the configured per-session and per-process
request rates measured in a rolling 15-second window. Defaults are
`http-session-rate-limit: 5` and `http-service-rate-limit: 100` requests per
second. Before an MCP session is established, only the process-wide limit
applies.

The limiter SHALL use FastMCP's live Streamable HTTP session registry to decide
whether a supplied session identifier is established. It SHALL not retain local
counter state for unknown identifiers and SHALL remove a session counter after
its rolling window expires.

The session limit SHALL return HTTP 429; the process-wide limit SHALL return
HTTP 503. Both SHALL include `Retry-After` for the earliest expiring admitted
request. Rejected requests SHALL not consume capacity, so retries become
available naturally as the rolling window expires. Stdio SHALL not use this
limiter.

#### Scenario: An established session reaches its request capacity
- **WHEN** an HTTP request would exceed the session's 15-second capacity
- **THEN** the server returns HTTP 429 with `Retry-After`
