## 1. Specification prerequisite

- [ ] 1.1 Repair the pre-existing structural delta header in `openspec/specs/knowledge-export/spec.md` so the export-authorisation delta can archive; verify strict OpenSpec validation reports no target-spec archive blocker.

## 2. Authentication configuration and policy

- [ ] 2.1 Add HTTP(S)-only server authentication configuration and a bearer-credential provider that resolves a redacted principal and immutable `user`/`admin` scopes from secret references; verify configuration parsing never serialises or logs credentials and disabled authentication leaves unprotected HTTP(S) calls available.
- [ ] 2.2 Implement transport-aware authorisation types, stable authentication-required and insufficient-scope results, and the `admin`-implies-`user` hierarchy; verify unit tests cover every scope decision, absent credentials, invalid credentials, and trusted stdio.
- [ ] 2.3 Define the complete tool-registration scope map, including every persisted project-configuration mutation and SQLite document-ingestion callback as `user`, plus global flags, document updates, and exports as `admin`; verify a registry-level regression test fails if the expected protected-operation map changes.

## 3. HTTP(S) and request-context boundary

- [ ] 3.1 Integrate the configured provider through supported FastMCP/ASGI HTTP(S) extension points before protected application dispatch; verify HTTP integration tests cover valid credentials, missing/invalid credentials, insufficient scope, and an unprotected request without credentials.
- [ ] 3.2 Propagate only immutable transport kind, principal identifier, and scopes into `RequestContext`; verify request-context tests prove raw credential material and transport request objects are unavailable to application handlers.
- [ ] 3.3 Enforce registered required scopes in the tool wrapper after argument validation but before session creation, project binding, or handler execution, including the conditional SQLite-ingestion branch of `send_file_content`; verify an unauthorised `set_project` call cannot mint a session or persist a binding and a non-ingestion callback remains unprotected.

## 4. Apply the protected-operation policy

- [ ] 4.1 Apply `user` scope metadata to project binding, selection, cloning, project feature flags, categories, collections, permission paths, exports configuration, every other persisted project-configuration mutation, and `send_file_content` when it requests SQLite document ingestion; verify parameterised tool tests distinguish HTTP(S) unauthenticated, `user`, and `admin` callers while stdio remains unrestricted.
- [ ] 4.2 Apply `admin` scope metadata to global feature-flag mutation, `update_documents`, and `export_content`; verify each rejected HTTP(S) invocation returns no mutated configuration, docroot write, or exported content.
- [ ] 4.3 Preserve unauthenticated access to the explicitly unprotected HTTP(S) MCP surface; verify discovery and selected read-only operations retain their current responses without credentials.

## 5. Documentation and full verification

- [ ] 5.1 Document HTTP(S) authentication enablement, secret-reference handling, scope assignment, protected-operation inventory, and rollback; verify installation guidance states that stdio never requires authentication.
- [ ] 5.2 Add end-to-end transport tests for the complete HTTP(S) and stdio authorisation matrix, including an authenticated `user` project mutation and an authenticated `admin` server mutation; verify all cases run against the actual ASGI server.
- [ ] 5.3 Run the targeted authentication, transport, request-context, and protected-tool tests, then the repository quality checks required by the change; verify all commands pass and no credentials appear in test output or fixtures.
