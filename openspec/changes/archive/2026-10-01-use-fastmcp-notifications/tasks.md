## 1. Notification extension contract

- [ ] 1.1 Define the `io.uniquode/mcp-guide-instructions` extension and typed `notifications/instructions/dispatch` payload, then verify capability negotiation and payload serialisation with unit tests
- [ ] 1.2 Register the extension only for MCP `2026-07-28` sessions and verify non-negotiating modern clients retain response-metadata instruction delivery without receiving the custom notification

## 2. Session-owned queued delivery

- [ ] 2.1 Refactor task-manager instruction dispatch into reserve, confirm, and release operations while preserving tracked-instruction callbacks and acknowledgement behaviour; verify success and failed-send paths with focused unit tests
- [ ] 2.2 Deliver a reserved modern instruction through the owning FastMCP request stream and verify another session cannot receive or consume it
- [ ] 2.3 Retain pending modern instructions when no owning request stream is active and verify delivery on the next request from that same client

## 3. Response boundary and compatibility

- [ ] 3.1 Select notification delivery for negotiated modern clients and `mcp-guide.instructions` metadata fallback for non-negotiating modern clients across tool, prompt, and resource adapters while preserving independent cache metadata; verify each response surface
- [ ] 3.2 Preserve legacy structured `additional_agent_instructions` delivery and verify legacy acknowledgement and retry behaviour remain unchanged
- [ ] 3.3 Reshape the rendered `_system/_startup` template with unconditional local workflow-context scope and delivery-purpose guidance, remove its `startup-instruction` requirement gate, and verify it queues on every first project binding
- [ ] 3.4 Update developer protocol documentation to distinguish notification delivery, metadata fallback, stream deferral, client-controlled handling, and legacy compatibility; verify documented examples match the tested contract

## 4. Integration verification

- [ ] 4.1 Add integration coverage for successful response, failure response, background queueing, failed notification send, and cross-session isolation; verify the focused suites pass
- [ ] 4.2 Run formatting, linting, type checking, strict OpenSpec validation, and the foreground full pytest suite; record results
