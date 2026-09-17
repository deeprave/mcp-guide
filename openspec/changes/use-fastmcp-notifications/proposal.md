## Why

Modern Guide responses currently place queued `additional_agent_instructions` in
response metadata. This attaches agent-directed natural language to an otherwise
unrelated tool, prompt, or resource response, which resembles instruction
injection and makes the delivery channel harder for clients to reason about or
trust.

Guide should use FastMCP's server-to-client notification API for modern MCP
sessions instead. A notification is an explicit state-delivery mechanism, not
part of the requested result. It also makes clear that the client, rather than
the server, decides how to surface or act on an instruction.

## What Changes

- Add a negotiated Guide instruction-notification capability for modern MCP
  clients, using FastMCP's notification API to deliver queued additional agent
  instructions outside tool, prompt, and resource response metadata.
- Retain a pending notification when no suitable stream for its owning client is
  active, then deliver it through that client's next request stream without
  routing it through another session.
- Remove modern `mcp-guide.instructions` response metadata delivery for clients
  that negotiate notification support, while preserving it as a delivery
  fallback for modern clients that do not and preserving the legacy structured
  `additional_agent_instructions` compatibility contract.
- Keep notification payloads session-owned, bounded to the queued instruction,
  and separate from logging or arbitrary task output.
- Document the transport limitation: sessionless Streamable HTTP may defer a
  background notification until the owning client next makes a request.
- Render unconditional startup guidance from the existing `_system/_startup`
  template after a Session first binds, explaining Guide's local
  workflow-context scope and the limited purpose of its delivered guidance.

## Capabilities

### New Capabilities

- `agent-instruction-notifications`: negotiated, session-owned FastMCP
  notification delivery for queued Guide agent instructions.

### Modified Capabilities

- `response-metadata`: replace modern response-metadata instruction delivery
  with negotiated notification delivery while retaining legacy behaviour.
- `task-manager`: preserve queued-instruction ownership and acknowledgement
  semantics when modern delivery is deferred to the owning client's request
  stream, including unconditional rendered startup guidance.
- `tool-infrastructure`: adapt modern tool, prompt, and resource response paths
  so they dispatch notifications without embedding queued instructions in their
  result metadata when the client negotiated notification support.

## Impact

- Affected code: `mcp_result_adapter.py`, the task manager, session/request
  lifecycle, FastMCP notification integration, modern response adapters, and
  the rendered `_system/_startup` template.
- Affected protocol surface: a new Guide-negotiated notification extension for
  modern clients; notification delivery supersedes
  `_meta["mcp-guide"]["instructions"]` when negotiated.
- Legacy clients retain the existing structured
  `additional_agent_instructions` payload.
