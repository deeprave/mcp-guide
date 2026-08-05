## 1. Protocol Baseline and Dependency Selection

- [ ] 1.1 Create protocol fixtures from the checked-in `2026-07-28` schema for discovery, tool, prompt, resource, stdio, and Streamable HTTP flows.
- [ ] 1.2 Evaluate available Python MCP SDK and FastMCP releases against those fixtures; record the selected versions, supported APIs, and any required compatibility shims.
- [ ] 1.3 Define the supported protocol-revision policy and decide whether a time-bounded legacy bridge is required.
- [ ] 1.4 Add dependency constraints and lockfile updates only after the compatibility spike demonstrates the selected APIs.

## 2. Request Context and State Boundary

- [ ] 2.1 Define framework-neutral request-context, response-metadata, owner-key, and project-identity types.
- [ ] 2.2 Implement extraction of negotiated revision, request identity, roots, client metadata, and agent metadata through the selected SDK's public APIs.
- [ ] 2.3 Implement integrity-protected, expiry-bound request state with principal/request binding and versioned payloads.
- [ ] 2.4 Add unit tests for context extraction, missing project context, state round trips, tampering, expiry, and concurrent owner isolation.
- [ ] 2.5 Remove server-PWD project inference from remote request resolution while retaining explicit project selection behavior.

## 3. Server and Transport Entry Points

- [ ] 3.1 Refactor server construction into a v2-supported application/server factory with process-only startup hooks.
- [ ] 3.2 Replace stdio startup with the selected v2-supported runner and add modern stdio interoperability tests.
- [ ] 3.3 Replace the Streamable HTTP wrapper with the selected v2-supported handler and validate endpoint, negotiation, header, TLS, and error behavior.
- [ ] 3.4 Implement response metadata handling for request state and conservative cache hints, with tests for cacheable and non-cacheable responses.
- [ ] 3.5 Remove private FastMCP/MCP lifecycle assumptions from server startup and transport code.

## 4. Project Context and Lifecycle Migration

- [ ] 4.1 Refactor `Session` access so durable project configuration is independent of a FastMCP connection object.
- [ ] 4.2 Replace bootstrap and active-session correctness paths with explicit request-context propagation.
- [ ] 4.3 Remove the weak registry keyed by `MiddlewareServerSession` and the private `_handle_message` roots-change monkeypatch.
- [ ] 4.4 Implement request-driven project rebinding from roots or validated state and preserve defined no-project behavior.
- [ ] 4.5 Add concurrency and project-switch tests covering independent requests, absent roots, and stateful project selection.

## 5. MCP Surface Adaptation

- [ ] 5.1 Implement the common adapter from internal `Result` and rendered content to SDK-native tool, prompt, and resource responses.
- [ ] 5.2 Migrate tool registration and decorators to inject request context and stop JSON-string serialization at the SDK boundary.
- [ ] 5.3 Migrate prompt registration and rendering to request context and the common result adapter.
- [ ] 5.4 Migrate guide resource and command URI handling to request-scoped URI extraction without FastMCP internal request objects.
- [ ] 5.5 Add regression tests proving embedded instructions, `additional_agent_instructions`, errors, and dispositions survive each public MCP surface.

## 6. Task Manager and Background Work

- [ ] 6.1 Partition pending instructions, acknowledgements, caches, and project-scoped task state by explicit owner and project keys.
- [ ] 6.2 Refactor task lifecycle APIs to accept explicit context ownership rather than reading an ambient MCP session.
- [ ] 6.3 Redesign roots-dependent and other server-to-client flows to use supported multi-round-trip input where needed, or retire them with documented behavior.
- [ ] 6.4 Define expiry and cleanup behavior for undeliverable instructions and invalid interaction state.
- [ ] 6.5 Add task-manager tests for concurrent clients/projects, project switches, background delivery, expiry, cleanup, and cancellation.

## 7. Verification, Documentation, and Release

- [ ] 7.1 Run protocol contract and interoperability tests against both stdio and Streamable HTTP with supported clients.
- [ ] 7.2 Run full unit, integration, concurrency, security, lint, and type-check suites; resolve regressions before release.
- [ ] 7.3 Document the supported protocol revisions, client migration instructions, HTTP requirements, state behavior, and any legacy bridge end date.
- [ ] 7.4 Add release notes covering breaking changes, deployment/rollback steps, and configuration changes.
- [ ] 7.5 Validate the completed OpenSpec change against the implemented behavior before archive.
