## 1. Request-context foundation

- [ ] 1.1 Define the resolved application `RequestContext` model, including validated interaction ownership, protocol/client data, Session, optional `RootIdentity`, optional exact active `Project`, and response metadata facilities; verify focused context-model tests cover bound and unbound construction.
- [ ] 1.2 Remove the redundant `ActiveConfiguration` shape and update all consumers to read the immutable active `Project` from `RequestContext`; verify no production import or reference remains.
- [ ] 1.3 Add explicit request-context helper APIs for required project/root access, task-result processing, and runtime-owned operations; verify unbound helpers fail with clear errors and bound helpers delegate to their supplied Session.
- [ ] 1.4 Implement the single public-boundary resolver that validates an interaction and creates one `RequestContext`; verify a nested operation receives the same Session and Project instance without another session lookup.

## 2. Runtime and Session ownership

- [ ] 2.1 Keep `ConfigManager` private to `GuideRuntime` and add runtime façade methods for application configuration access, including a docroot accessor that returns the manager's current value without runtime caching; verify a configuration reload is visible through the façade.
- [ ] 2.2 Define Session operations for binding and replacing the immutable active Project, and ensure context construction reads the exact selected Project; verify an in-request configuration update uses the returned replacement Project for later work.
- [ ] 2.3 Convert independently scheduled/background work to receive its owning Session explicitly; verify it cannot select a Session from task-local ambient state.

## 3. Public MCP boundaries and delegated handlers

- [ ] 3.1 Refactor tool registration/decorators so raw FastMCP context is converted once at the boundary and all tool implementations receive `RequestContext`; verify an integration tool call preserves the same Session through delegated content, category, and collection operations.
- [ ] 3.2 Refactor prompt registration, command routing, help, content lookup, rendering, template access, and result processing to accept and propagate the same `RequestContext`; verify a prompt with an interaction identifier never performs a second session resolution.
- [ ] 3.3 Refactor Guide URI resource and command handlers to construct/use `RequestContext` at their public boundary and retain it through content/command delegation; verify a resource request retains validated interaction ownership and active Project.
- [ ] 3.4 Convert every remaining production helper that accepts raw FastMCP context or calls session-resolution helpers to accept `RequestContext` or an explicit Session; verify repository searches find no raw FastMCP context below public adapters and no nested implicit session resolution.

## 4. Remove ambient fallbacks and update tests

- [ ] 4.1 Delete production Session/TaskManager `ContextVar` ownership and fallback APIs, including any transient-session allocation path used when propagation is absent; verify missing context/Session is a clear hard error.
- [ ] 4.2 Update unit and integration fixtures to construct resolved request contexts or pass explicit Sessions, without a production compatibility shim; verify focused tests cover concurrent nested operations retaining separate Session/Project pairs.
- [ ] 4.3 Add regression coverage for tool, prompt, and resource delegation so a supplied interaction cannot be dropped or replaced by an unbound/transient Session; verify the relevant focused test modules pass.

## 5. Full verification

- [ ] 5.1 Run formatting and static checks with `uv run ruff format --check` and `uv run ruff check --no-cache`, and resolve all findings.
- [ ] 5.2 Run `uv run pytest` in a foreground PTY and verify the complete test suite passes without hanging.
- [ ] 5.3 Validate the completed change with `openspec validate use-request-context --strict --no-interactive` and verify `git diff --check` reports no whitespace errors.
