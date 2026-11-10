# Tasks

## 1. Rendered form invocation

- [ ] 1.1 Add the asynchronous `elicit` section extension so a reached section selects one declared form, awaits unresolved input, and renders its enclosed content with resolved keyword values; extend existing renderer and elicitation tests for selected, unselected, accepted, and fallback paths.

## 2. Interactive entrypoint delivery

- [ ] 2.1 Route command and skill form delivery through rendered invocations, retaining existing validation, URI precedence, continuation, and MCP protocol behaviour; update existing command and skill tests for conditional and partial form selection.

## 3. Template migration

- [ ] 3.1 Convert shipped interactive templates and form-bearing partials to explicit `elicit` sections, and remove preflight-only elicitation collection; verify the affected rendering and integration tests.
- [ ] 3.2 Update developer documentation to explain form declarations, rendered `elicit` invocation, accepted-value scope, and migration from preflight-only partials; verify the examples match shipped templates.
