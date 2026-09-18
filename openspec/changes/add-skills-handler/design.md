## Context

Guide URLs expose curated project content, while Codex ordinarily discovers local
skills from its host-provided catalogue. Before designing a complete package
system, Guide must establish whether explicit retrieval of a skill resource is
enough for Codex to follow that skill in a real task.

## Goals / Non-Goals

**Goals:**
- Serve one bundled skill entrypoint through an explicit Guide resource.
- Let an agent inspect minimal catalogue metadata and deliberately retrieve that
  entrypoint.
- Confirm in a real Codex task that the retrieved instructions are followed.
- Use the observed result to decide whether a broader package system is viable.

**Non-Goals:**
- Automatic local package installation, server-side script execution, imports, exports,
  and agent-specific filesystem mappings.
- Automatic native-skill discovery or selection by Codex.
- Building the MCP v2 engine migration as part of this change.
- Server-side script execution.

## Decisions

- Use the existing Guide resource mechanism and the normal Guide tool
  registration pattern rather than waiting for MCP v2 or adding a new command
  pipeline. `list_skills` and `guide://$` share one catalogue implementation.
- Reserve leading `_`, `$`, and `!` characters in category and collection names. Expose the skills
  catalogue at `guide://$`. Each skill is a flat package directly below `_skills`, rooted at
  `SKILL.md` (or the renderable server source `SKILL.md.mustache`). For example,
  `_skills/workflow-status/SKILL.md.mustache` is the `workflow-status` package and
  `guide://$workflow-status` retrieves its rendered `workflow-status/SKILL.md` entrypoint.
  Package members are individually retrievable below the same URI root, including
  `resources/`, `agents/`, and `scripts/`. Nested package roots are not discovered, keeping
  the package name portable to standard local Codex skill layouts.
- All rendered package files receive a `skill` template context derived from the public
  package identity: `path`, `entrypoint`, `uri`, `resources_uri`, `scripts_uri`, and
  `agents_uri`. Server filesystem paths and template suffixes are never exposed.
- Every package-file response places the public rendered path in `Result.message` and
  the rendered content in `Result.value`. A script member is retrievable information,
  not an executable: the entrypoint tells a client to download, inspect, establish trust,
  and obtain authority before running it locally.
- Package the five Guide workflow phases with portable verb names:
  `workflow-check`, `workflow-discuss`, `workflow-explore`,
  `workflow-implement`, and `workflow-plan`. Each uses the rendered
  `workflow-file` context value rather than a hard-coded `.guide.yaml` path.
  Keep `workflow-status` deliberately narrow: when workflow mode is enabled,
  it reads and reports only the configured workflow file. When workflow mode
  is disabled, it reports that state without naming or inspecting a workflow
  file.
- Let skill entrypoints declare MCP forms in their `elicitation` frontmatter.
  The shared resource resolver validates only primitive form fields, requests
  required values through capability-negotiated MCP elicitation, and merges an
  accepted response into the existing keyword template context. URI keywords
  satisfy the same required fields without a form. Complete standard JSON
  Schema defaults provide a safe fallback when elicitation is unavailable or
  cancelled. A form may instead declare `fallback: render`, which renders the
  entrypoint without unresolved values so its instructions can obtain them.
  Defaults are surfaced to templates as defaulted-form context. This applies
  to every declared skill rather than a named package.
- Provide `workflow-review` as a separate phase skill. In workflow mode it
  moves the workflow file to `review`; in OpenSpec mode it validates the active
  change. Its declared `review-target` form requests a `mode` selection when
  absent. If the form cannot be completed, its `fallback: render` instructions
  direct the agent to present a client-native choice picker for uncommitted
  work, `main`, a branch, or a pull request, and to wait for the user's
  selection. It accepts a `mode` query value selecting `uncommitted`, `main`, a branch, a
  pull-request URL, or a pull-request number for the current repository. It obtains two fresh,
  independent reviews, using a heavier model at medium or high effort and a
  lighter model at its highest supported effort. Each reviewer receives only
  the selected target, repository evidence, applicable guidance and OpenSpec
  artefacts, and the report contract: it does not receive or inspect previous
  conversations, review records, collated inventories, or another reviewer's
  findings. The coordinator collates only the two reports created for that
  review after both have completed. Review completes from the evidence needed
  for its selected scope; reviewers may use targeted commands to investigate a
  suspected defect or claimed behaviour. For a pull-request target, the
  coordinator examines existing pull-request comments only after those fresh
  reviews finish, marking matching combined findings as already flagged or
  adding useful context without changing source reports.
  It presents the collated inventory through `just-one` when the user elects
  that workflow or has an established preference for sequential triage;
  otherwise it uses the user's requested or ordinary review presentation.
- Provide `just-one` as the user-facing finding-triage skill. It presents the
  complete fixed inventory one finding at a time from P1 through P6, records
  each accept, decline, discussion outcome, or variation in the canonical
  combined review JSON record, and never changes code during triage. After every
  finding has a recorded disposition, it presents the accepted action list and
  requires the user's explicit confirmation before carrying it out.
- Treat review reports as durable, shared workflow data rather than transient
  prose. Each independent reviewer writes a fresh source report to
  `{{path.documents}}Reviews/<issue>/<agent-name>.json`; the workflow file's
  required `issue` field is the sole review key. Before dispatch, the
  coordinator determines each reviewer's next version without exposing earlier
  findings, so its report can overwrite the previous report while its findings
  carry that version. An empty issue value means there is no active workflow
  issue, so review dispatch and triage stop. After collation, the coordinator
  writes `{{path.documents}}Reviews/<issue>.json` as the canonical inventory.
  It references source reports and versions, stores combined finding details
  and triage fields, and is the only review artefact triage updates. This keeps
  independently produced reports intact while giving a later agent a common
  input for implementation hand-off.
- Treat selection as explicit: the user or agent requests the named skill, then
  Codex reads it through Guide and follows it for the current task. Catalogue
  responses are `agent/information` by default so an agent can inspect
  availability without executing a skill. The standard `list_skills` tool
  accepts `verbose=true` to deliberately return the same catalogue as
  `user/information` for a user-facing list, while `table=true` returns that
  user-facing catalogue as a Markdown table through either entrypoint. Skill URI query parameters follow
  the same parsing and template-context path as command URI query parameters:
  templates receive `kwargs` and `raw_kwargs`, and a valueless key is `true`.
  Thus `guide://$?verbose` reaches the catalogue loader while named skills can
  use arbitrary parameters. Native MCP resource reads preserve the complete
  URI before that shared parser runs; template-declared transport parameters
  must not discard skill keywords. A selected skill entrypoint defaults to
  `agent/instruction`; its declared document disposition remains available for
  future skill package types. The Guide prompt also
  recognises a leading `$` as an explicit skill selection and delegates it to
  the same resolver as `read_resource`, rather than treating it as a content
  expression. It likewise recognises `_` as the URI-compatible command
  prefix, while retaining `:` and `;` for existing prompt command syntax.
- Apply the same active-project boundary to every Guide prompt before prompt
  routing or task-manager activity. Optional local stdio PWD binding may
  establish that project first; otherwise the prompt returns the standard
  `no_project` result and does not render status, command, content, or skill
  output against an empty project.
- Exercise that path in a real Codex session. Focused tests prove resource
  routing and rendering, while the session exercise establishes whether Codex
  honours the delivered instructions.

## Risks / Trade-offs

- [Codex does not honour resource-delivered skills] → stop after the proof and
  assess a small local bootstrap skill instead of building exports.
- [A skill needs supporting files] → retrieve the explicitly named member from its
  package; reject paths that escape the package root.
- [MCP v2 rollout timing] → do not couple the proof to the engine migration.

## Experimental MCP skills extension

The successful explicit-selection proof justifies exposing skills as a complete,
opt-in MCP extension rather than a passive capability hint. The extension does
not replace Guide's interoperable resource and tool paths: those remain the
fallback for clients that do not implement the extension.

The server and client negotiate the namespaced
`io.uniquode/mcp-guide-skills` extension during initialisation. For an
opted-in client, the extension provides an additive `skills/list` request and
`notifications/skills/list_changed` notification. `skills/list` requires the
opaque Guide `session_id` and returns a `skills` array whose entries carry the
same identifier, name, description, usage, and URI information as the ordinary
Guide catalogue. The notification carries no payload.
The client refreshes its native skill registry by calling `skills/list` after
receiving the notification. Guide sends that notification only to the affected
connection after its effective skills change; it does not send it to clients
that did not negotiate the extension.

Skill availability is scoped to the connection's active, bound Guide session,
because requirements and feature flags can differ by project. `skills/list`
therefore returns only the skills currently usable for that session. A change
to the bound project, a relevant effective feature flag, or the discoverable
skill set causes a notification only when it actually changes that effective
list. Project replacement preserves the negotiated extension subscription and
its last effective list on the active replacement Session; it never transfers
project-local task, rendering, or instruction state. An unbound session has no
effective skill set to expose through the extension.

`skills/list` and its notification are deliberately non-standard extension
methods. The extension capability is the compatibility contract that prevents
an ordinary MCP client from being expected to understand them. The existing
`list_skills` tool and `guide://$` catalogue remain independently usable by
legacy and non-participating clients.

### Configuration boundary

`mcp-skills` is a global boolean feature flag, defaulting to `false`. It is
read while the server is constructed, before capability negotiation. It is
invalid in project-level configuration: a project is not necessarily known at
negotiation time, and an advertised server capability must not vary after a
client has connected. Changing the flag requires a Guide restart.

The flag gates the entire extension, not merely an informational capability
field. When false, Guide neither advertises the extension nor serves
`skills/list` or emits `notifications/skills/list_changed`. When true, it
advertises the extension and enables both operations for clients that
negotiate it.

### Compatibility boundary

When disabled, Guide does not advertise the extension. When enabled, modern
MCP negotiation advertises the namespaced skills extension and its supported
operations. Any retained `capabilities.experimental.skills` field is only a
compatibility hint; it must not be the sole contract for `skills/list` or
list-change notifications. The underlying Guide skill catalogue and URI
resolution remain available independently, so clients that do not implement
the extension can use the standard Guide resource and tool paths.

### Accepted review remediations

Skill package members are literal paths, not document patterns. The resolver
rejects glob syntax, absolute paths, and traversal segments before rendering;
an unknown or ambiguous member produces the same structured `not_found` result
as an unknown package.

The extension records a skills-list snapshot only after the owning session's
connection receives `notifications/skills/list_changed`. A configuration
callback without that connection's active request context leaves the changed
list pending. The next request for that same session flushes the pending
notification; a request for another session never receives it.

The generic Guide resource route preserves the original URI for both command
and skill namespaces. It passes the current MCP context to skill resolution so
frontmatter elicitation behaves identically for generic and dedicated skill
resource routes.

Interaction-wide protocol subscriptions use the shared Guide session-listener
lifecycle rather than optional duck-typed callbacks. A listener declares
whether it is session-scoped or interaction-scoped. Session replacement
recreates session-scoped listeners with the replacement Session and transfers
interaction-scoped listeners before their replacement callback runs. This
preserves a negotiated skills subscription without transferring task,
rendering, or instruction state, and provides one lifecycle contract for later
Guide protocol extensions.
