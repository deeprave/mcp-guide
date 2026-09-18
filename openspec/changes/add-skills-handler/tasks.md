## 1. Explicit Codex skill-use proof

- [x] 1.1 Reserve leading `_`, `$`, and `!` characters in category and collection names for internal namespaces
- [x] 1.2 Add the minimal `guide://$` catalogue and standard `list_skills` tool through the dedicated Guide skill resource namespace, with stable IDs, purpose, and entrypoint URIs
- [x] 1.3 Add one self-contained bundled skill entrypoint selected from that catalogue
- [x] 1.4 Preserve project-aware rendering and return clear errors for unknown skill identifiers
- [x] 1.5 Add focused client-facing catalogue and entrypoint resource tests without coupling tests to rendered templates
- [x] 1.6 Validate in a real Codex task that an explicitly selected Guide skill is retrieved and followed; record the result
- [x] 1.7 Return the skill catalogue as agent information by default, with an explicit user-information view from `list_skills(verbose=true)`
- [x] 1.8 Preserve skill URI query parameters and forward `guide://$?verbose` to the catalogue loader
- [x] 1.9 Preserve arbitrary skill URI query parameters through native resource transport and forward them into the shared command-compatible template keyword context
- [x] 1.10 Route `$`-prefixed Guide prompt requests through the shared skill resolver, and `_`-prefixed requests through command dispatch, preserving URI-compatible path and query arguments
- [x] 1.11 Reject every unbound Guide prompt at the shared prompt boundary before routing or task-manager activity

## 2. Experimental MCP skills extension

- [x] 2.1 Add the global-only, startup-scoped boolean `mcp-skills` feature flag, rejecting project-level use
- [x] 2.2 Advertise the experimental additive skills capability only when `mcp-skills` is enabled at server construction
- [x] 2.3 Verify capability serialisation and global/project flag behaviour with focused tests
- [x] 2.4 Define and negotiate the `io.uniquode/mcp-guide-skills` MCP
  extension for modern clients, retaining any existing experimental capability
  field only as a compatibility hint
- [x] 2.5 Implement the extension's `skills/list` request, gated by
  `mcp-skills`, client extension negotiation, and the active bound Guide
  session
- [x] 2.6 Track the effective skills for each negotiated active session,
  preserve that protocol subscription across project Session replacement, and
  send `notifications/skills/list_changed` only when its effective list changes
- [x] 2.7 Ensure a disabled `mcp-skills` flag prevents capability
  advertisement, `skills/list`, and skills-list notifications while preserving
  the ordinary Guide tool and resource catalogue
- [x] 2.8 Add focused extension conformance tests for negotiation, session
  scoping, feature-flag gating, refresh notifications, and no-op changes

## 3. Packaged skill resources

- [x] 3.1 Discover only `SKILL.md` package roots and derive Guide skill identifiers from their package paths
- [x] 3.2 Render entrypoints and named package members through the shared package root, exposing public virtual paths in `Result.message` and a package-aware `skill` template context
- [x] 3.3 Preserve package containment and retrieve script members without executing or trusting them
- [x] 3.4 Convert the bundled workflow-status skill and focused integration fixtures to the package layout, with behaviour tests for entrypoints, members, context, and rejected escapes

## 4. Workflow skill packages

- [x] 4.1 Port the five Guide workflow phases as flat, verb-named skill packages: `workflow-check`, `workflow-discuss`, `workflow-explore`, `workflow-implement`, and `workflow-plan`
- [x] 4.2 Simplify `workflow-status` to workflow-file reporting only, and expose the configured workflow file to skill templates with `.guide.yaml` as its default
- [x] 4.3 Add a user-facing `table=true` catalogue view for both `list_skills` and `guide://$`
- [x] 4.4 Read required skill `usage` frontmatter and include it in every catalogue representation

## 5. Review and finding-triage skills

- [x] 5.1 Extend the skill design and specification for workflow review targets,
  independent review collation, and deferred finding disposition
- [x] 5.2 Add the flat `workflow-review` package, including workflow review
  transition, strict OpenSpec validation, target selection, and two independent
  review instructions
- [x] 5.3 Add the flat `just-one` package, including P1-to-P6 one-at-a-time
  presentation, transient todo-list decisions, and explicit confirmation before
  implementing accepted actions
- [x] 5.4 Use one frontmatter-declared, capability-negotiated MCP elicitation
  path for native resource and `read_resource` tool requests before rendering
  an entrypoint, merging accepted primitive fields into template keywords and
  applying complete declared schema defaults when a caller cannot elicit or
  cancels, while retaining explicit required-keyword guidance otherwise
- [x] 5.5 Record each independent workflow review in a per-reviewer JSON report
  under the shared documents review directory, and have `just-one` preserve
  user decisions and variations in those records
- [x] 5.6 Require fresh, isolated reviewer inputs and reports: reviewers neither
  receive nor inspect previous conversations or adjacent review records, and
  collation uses only the two reports created for the current review
- [x] 5.7 Remove the obsolete instruction to cease review on failed basic
  checks, leaving reviewers to use the evidence needed for their selected scope
- [x] 5.8 Preserve independent source reports under `Reviews/<issue>/` with
  per-reviewer finding versions, and use `Reviews/<issue>.json` as the
  canonical combined inventory updated during finding triage
- [x] 5.9 Keep independent pull-request reviews isolated from earlier comments,
  then have the coordinator annotate only the combined inventory after collation

## 6. Accepted review remediations

- [x] 6.1 Treat skill package members as literal paths, rejecting glob syntax
  and returning structured `not_found` errors for missing or ambiguous members
- [x] 6.2 Preserve deferred skills-list notifications until the owning session
  can receive them, then flush them on that session's next request
- [x] 6.3 Keep `workflow-status` limited to conditional workflow-file status
  reporting and align the design and specification
- [x] 6.4 Return structured validation errors for invalid skill catalogue URI
  arguments
- [x] 6.5 Preserve generic Guide command and skill resource URI routing and
  pass MCP elicitation context through the generic skill route
- [x] 6.6 Preserve arbitrary skill URI query parameters through native resource
  registration, with a regression covering named and valueless keywords
- [x] 6.7 Replace optional session-listener lifecycle duck typing with explicit
  session and interaction listener scopes, transferring only protocol-scoped
  subscriptions on project replacement
- [x] 6.8 Apply shared URI-safe category and collection name validation to
  skill package identifiers and public skill `name` frontmatter values
- [x] 6.9 Isolate malformed, invalid, and unreadable skill packages so they
  are logged and skipped without hiding valid catalogue entries
- [x] 6.10 Cache skill catalogue discovery with command-style generations and
  recursive mtime checks, then notify an owning negotiated session on its next
  request only when its effective catalogue changed
