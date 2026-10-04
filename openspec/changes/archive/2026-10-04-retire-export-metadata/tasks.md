# Tasks

## 1. Remove export-derived project state

- [x] 1.1 Remove the export-tracking model, project serialisation, configuration update handling, and project-copy handling; accept legacy `exports` data on load and verify a subsequent save omits it.
- [x] 1.2 Remove the export-reference branch and metadata-bypass semantics from ordinary content retrieval; verify `get_content` and equivalent content URIs return Guide-rendered content for the same expression/pattern after export and when legacy tracking exists.

## 2. Make export a client-owned hand-off

- [x] 2.1 Simplify `export_content` to return rendered payload and delivery frontmatter with a client-supplied destination covered by configured `allowed_write_paths`; reject disallowed destinations without adding permissions, selecting default directories, checking the client filesystem, calculating metadata hashes or mutating configuration. Ensure implicit temporary-path exceptions do not bypass configured export paths; verify state remains unchanged on success and denial.
- [x] 2.2 Remove `list_exports`, `remove_export`, their command templates and formatting templates, the otherwise unused export-list display-option helper, `path-export`, agent-specific knowledge-directory defaults, and related documentation; verify MCP tool and command discovery no longer exposes the retired interfaces.
- [x] 2.3 Remove export's temporary mutation-based user-scope gate and align ADR-014 and the canonical authentication spec via this change's delta; keep write-path validation independent of authentication and leave archived authentication artefacts unchanged.
- [x] 2.4 Audit all active instructions/text for direct and subtle tracking dependencies: tool schemas/docstrings and result instructions, command/system templates, feature-flag/context documentation, examples, URI guidance and diagrams. Remove prior-export/indexed-copy substitution, staleness/hash skip, metadata bypass, and automatic permission-grant guidance; update retained export/add guidance and preserve delivery frontmatter and client create/overwrite semantics.

## 3. Verify the boundary and compatibility

- [x] 3.1 Add behaviour-focused tests for stateless export, configured file/directory destinations and denied paths, unchanged permissions/configuration, legacy export configuration, ordinary tool/URI content retrieval after export, and retained export hand-off instructions using isolated fixtures. Do not assert literal production text; run targeted pytest files in the foreground.
- [x] 3.2 Run `openspec validate retire-export-metadata --strict`, applicable formatting and type checks, and the targeted export/content test suite; verify all pass.
- [x] 3.3 Reject filesystem-root write entries and lexical equivalents at shared project validation; verify configuration and permission additions cannot grant unrestricted filesystem coverage or persist denied changes.
- [x] 3.4 Reject ASCII controls, DEL and backticks in export destinations before creating delivery instructions; return fixed destination security errors without echoing rejected input and verify permitted destinations remain unchanged.
