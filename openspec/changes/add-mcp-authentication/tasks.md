## 1. Specification prerequisite

- [ ] 1.1 Repair the pre-existing structural delta header in `openspec/specs/knowledge-export/spec.md` so the export-authorisation delta can archive; verify strict OpenSpec validation reports no target-spec archive blocker.

## 2. Provider contract and policy

- [ ] 2.1 Add CLI configuration that selects an authentication-provider entry point and passes it an opaque configuration reference; verify no provider is constructed when the option is absent and no credential/reference value is serialised or logged.
- [ ] 2.2 Define asynchronous provider lifecycle, authorisation decision, optional handoff/challenge, and policy/revocation notification contracts; verify provider fixtures cover authorised, unauthenticated, forbidden, startup failure, key/policy change, and shutdown paths.
- [ ] 2.3 Define the complete protected-operation registry for tools, resources, and prompts: project configuration and conditional SQLite ingestion as `user`; global flags, document updates, and exports as `admin`; verify registry-level regression tests fail if the initial protected map changes.

## 3. Remote ingress and request-context boundary

- [ ] 3.1 Start and stop the selected provider with direct-TLS or explicitly configured trusted-proxy remote ingress; verify direct TLS passes ephemeral evidence to the provider and proxy mode rejects unverified/caller-controlled identity headers.
- [ ] 3.2 Integrate provider decisions before protected application dispatch without redirecting MCP requests; verify an unauthenticated protected operation receives a stable MCP-compatible result and preserves an opaque provider handoff where supplied.
- [ ] 3.3 Propagate only immutable transport kind, principal identifier, and scopes into `RequestContext`; verify raw credential material, provider internals, and transport request objects are unavailable to application handlers.
- [ ] 3.4 Enforce registered scope after argument validation but before session creation, project binding, sensitive resource/prompt reads, or handler execution; verify an unauthorised `set_project` cannot mint a session or persist a binding and a non-ingestion `send_file_content` callback remains unprotected.

## 4. Apply the initial protected-operation policy

- [ ] 4.1 Apply `user` scope metadata to project binding, selection, cloning, project feature flags, categories, collections, permission paths, exports configuration, every other persisted project-configuration mutation, and `send_file_content` when it requests SQLite ingestion; verify provider-backed remote tests distinguish anonymous, `user`, and `admin` callers while stdio remains unrestricted.
- [ ] 4.2 Apply `admin` scope metadata to global feature-flag mutation, `update_documents`, and `export_content`; verify every rejected remote invocation leaves configuration, document root, and exported content unchanged.
- [ ] 4.3 Preserve all existing remote operation responses when no provider is configured, and retain unprotected access when provider-backed policy is active; verify discovery and selected read-only operations retain their current responses.

## 5. Documentation and full verification

- [ ] 5.1 Document provider installation and CLI selection, direct-TLS and trusted-proxy requirements, handoff limits, secret/reference handling, scope inventory, rollback, and the absence of project-tenancy guarantees; verify documentation states that stdio never invokes a provider.
- [ ] 5.2 Add end-to-end transport tests against the actual ASGI server for direct TLS and trusted-proxy provider fixtures, including an authenticated `user` project mutation, authenticated `admin` server mutation, unauthenticated handoff, and unchanged stdio behaviour.
- [ ] 5.3 Run targeted provider, transport, request-context, and protected-operation tests, then the repository quality checks required by the change; verify all commands pass and no credentials or opaque references appear in test output or fixtures.
