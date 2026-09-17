## Context

See proposal.md for the motivation. Today, `TaskManager.process_result()` removes
the next queued instruction while processing an outgoing result, and modern
response adapters move that text into `_meta["mcp-guide"]["instructions"]`.
This makes an asynchronous instruction appear to be part of an unrelated
operation's response.

FastMCP provides `Context.send_notification()`. For an MCP 2026-07-28
sessionless connection, FastMCP relates the notification to the in-flight
request stream; it cannot reliably send an unrelated background notification
after that stream has ended. The existing skills extension already models the
required deferral pattern for list-change notifications.

## Goals / Non-Goals

**Goals:**

- Deliver modern queued agent instructions through an explicit FastMCP
  notification.
- Keep instruction delivery scoped to the owning Guide Session and request
  stream.
- Use notification delivery for clients that negotiate it, while retaining
  modern response-metadata delivery as a fallback for clients that do not.
- Preserve legacy response behaviour and task acknowledgement semantics.
- Render unconditional Session-startup guidance from the existing `_system/_startup`
  template when a project first binds.

**Non-Goals:**

- Make clients execute, display, trust, or acknowledge a notification.
- Create a generic server-to-client channel for arbitrary task data or logs.
- Guarantee immediate background delivery on a transport without a standing
  server-to-client stream.
- Change Guide's document or skill rendering dispositions.
- Render project-dependent startup templates before a Session has bound a
  project.

## Decisions

### Use a negotiated vendor extension and a typed notification

Guide will define the `io.uniquode/mcp-guide-instructions` extension for modern
clients. It will use `notifications/instructions/dispatch` with a compact typed
payload containing the instruction text and, when the instruction is tracked,
its opaque tracking identifier.

A custom event is preferable to `notifications/message`, which is logging-only,
and to resource updates, which communicate that a resource changed rather than
deliver one queued instruction. Extension negotiation ensures Guide does not
send an unknown method to an uninterested client.

### Retain metadata delivery for non-negotiating modern clients

The notification extension is additive. A modern client that does not negotiate
it will continue to receive the current `_meta["mcp-guide"]["instructions"]`
delivery. This prevents instruction loss while clients adopt the extension. A
negotiated client receives a notification instead of response metadata.

### Dispatch at the FastMCP request boundary, not in a response adapter

Response adapters will only serialise requested results and response metadata.
The resolved FastMCP request context will ask the Session task manager for the
next eligible instruction, send the notification through its own stream, then
confirm dispatch only after FastMCP reports success.

This keeps raw FastMCP access at the boundary and removes transport concerns
from `Result`, rendering, and response-formatting code.

### Use a reserve, confirm, and release delivery lifecycle

Task manager delivery will reserve an eligible instruction without treating it
as dispatched. A successful notification confirms dispatch and invokes any
existing dispatch callback; an unavailable stream or send failure releases the
reservation back to its owning Session's pending queue. Existing queue
serialisation will prevent duplicate concurrent delivery.

This replaces pop-before-send behaviour for modern notifications and preserves
the current retry and acknowledgement lifecycle.

### Retain legacy result delivery unchanged

Legacy protocol sessions will continue to obtain
`additional_agent_instructions` in their canonical structured Guide result.
Modern sessions that negotiate the new extension use notification delivery;
modern sessions that do not negotiate it retain the current metadata fallback.

### Use the rendered startup template for scope guidance

Guide will reshape the existing `_system/_startup` template and remove its
`requires-startup-instruction` gate. The session listener already renders and
queues that template when a project binds, so it can provide the scope guidance
through the same instruction path as other startup guidance.

This keeps instructions template-authored and renderable. It also ensures the
guidance is delivered only after an active project exists, where local workflow
context has a meaningful scope. FastMCP's static initialisation string remains a
generic server description rather than a second instruction source.

## Risks / Trade-offs

- [A client ignores or does not implement the extension] → retain the current
  response-metadata delivery until the client negotiates notification support.
- [A background task has no active stream] → retain the instruction and deliver
  it when the owning client next makes a request.
- [A notification send fails after a request starts] → release the reservation
  and preserve tracking state for a later retry.
- [A client interprets the notification as executable authority] → document
  that delivery is not acknowledgement or authorisation; client trust policy
  remains responsible for action selection.

## Migration Plan

1. Add the negotiated extension, typed notification, and session-owned
   notification dispatcher.
2. Refactor task-manager delivery to reserve, confirm, or release queued
   instructions.
3. Select notification or metadata delivery at the modern request boundary and
   retain legacy structured delivery.
4. Cover tool, prompt, resource, background, deferred, failure, and
   cross-session scenarios with focused integration tests.
5. Reshape the rendered startup template, remove its feature-flag gate, and
   verify it queues on every first project binding.
6. No persisted-data migration or compatibility configuration is required.
