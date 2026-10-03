# Tasks

## 1. Remove export-derived project state

- [ ] 1.1 Remove the export-tracking model, project serialisation, configuration update handling, and project-copy handling; accept legacy `exports` data on load and verify a subsequent save omits it.
- [ ] 1.2 Remove the export-reference branch from ordinary content retrieval and verify `get_content` always returns current Guide-rendered content after an export request.

## 2. Make export a client-owned hand-off

- [ ] 2.1 Simplify `export_content` to return rendered payload and delivery frontmatter with the client-supplied destination, without resolving paths, checking write permissions, calculating metadata hashes, or mutating project configuration; verify its state is unchanged before and after invocation.
- [ ] 2.2 Remove `list_exports`, `remove_export`, their command templates and formatting templates, `path-export`, agent-specific knowledge-directory defaults, and related documentation; verify MCP tool and command discovery no longer exposes the retired interfaces.
- [ ] 2.3 Reconcile the in-flight `add-mcp-authentication` operation inventory so it does not protect a retired export-state capability; validate that change's OpenSpec artefacts remain internally consistent.

## 3. Verify the boundary and compatibility

- [ ] 3.1 Add behaviour-focused tests for stateless export, client-owned destinations, legacy export configuration, and normal content delivery; run the targeted pytest files in the foreground.
- [ ] 3.2 Run `openspec validate retire-export-metadata --strict`, applicable formatting and type checks, and the targeted export/content test suite; verify all pass.
