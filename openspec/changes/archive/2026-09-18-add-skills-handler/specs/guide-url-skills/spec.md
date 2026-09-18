## ADDED Requirements

### Requirement: Packaged Guide skill serving
The system SHALL serve reusable Guide skills as package-shaped resources rooted
at `SKILL.md` through Guide resources for explicit selection by an agent. It
SHALL expose the catalogue through the standard `list_skills` tool registration
pattern and shall reserve leading `_`, `$`, and `!` characters in category and
collection names for internal namespaces.

#### Scenario: Serve a skill package entrypoint
- **WHEN** an agent requests a supported named skill for the current project
- **THEN** the system SHALL render that package's `SKILL.md` entrypoint through Guide
- **AND** the content SHALL be rendered for the current project and Guide
  settings
- **AND** the response `message` SHALL identify the rendered virtual path, such as
  `workflow-status/SKILL.md`
- **AND** the response `value` SHALL contain the rendered entrypoint content

#### Scenario: Serve a package member
- **WHEN** an agent requests a member below an available package, such as
  `guide://$workflow-status/resources/checklist.md`
- **THEN** the system SHALL render and return that member with its public virtual path
  in `message` and its content in `value`
- **AND** the member SHALL receive a `skill` template context containing the public
  package path and member URI roots
- **AND** a path that escapes the package root SHALL be rejected
- **AND** a member path containing glob syntax SHALL be rejected rather than
  treated as a document pattern
- **AND** an unknown or ambiguous member SHALL return a structured `not_found`
  result

#### Scenario: Retrieve a script safely
- **WHEN** an agent requests a package member below `scripts/`
- **THEN** the system SHALL return its content as a retrievable file
- **AND** SHALL NOT execute, install, or otherwise trust the script on behalf of the
  client

### Requirement: Skill catalog discovery
The system SHALL provide a minimal Guide skill catalogue containing the
metadata needed for an agent to explicitly select a skill.

#### Scenario: Inspect available skills
- **WHEN** an agent requests the catalogue through `list_skills` or `guide://$`
  through Guide's `read_resource` tool
- **THEN** the system SHALL list each available skill's identifier, description, and usage guidance from its frontmatter
- **AND** SHALL identify the resource URI for the skill entrypoint
- **AND** SHALL deliver the catalogue as `agent/information` content by default

#### Scenario: Isolate an invalid skill package
- **WHEN** one discovered skill package is unreadable, malformed, or has an
  invalid package identifier or public `name` value
- **THEN** the system SHALL log and exclude that package
- **AND** SHALL continue to return every independently valid skill package

#### Scenario: Use URI-safe skill identities
- **WHEN** Guide discovers a skill package
- **THEN** its package identifier and public `name` frontmatter value SHALL
  satisfy the shared category and collection name validation contract
- **AND** SHALL be safe to advertise and resolve in a `guide://$` URI without
  additional encoding

#### Scenario: Display available skills
- **WHEN** a caller requests `list_skills` with `verbose=true`
- **THEN** the system SHALL list the same available-skill catalogue
- **AND** SHALL deliver it as `user/information` content

#### Scenario: Display skills through a resource URI
- **WHEN** a caller requests `guide://$?verbose`
- **THEN** the system SHALL forward the URI query parameters to the skill
  catalogue loader
- **AND** SHALL deliver the catalogue as `user/information` content

#### Scenario: Display skills as a table
- **WHEN** a caller requests `list_skills(table=true)` or `guide://$?table`
- **THEN** the system SHALL return the available skills as a Markdown table
- **AND** each row SHALL contain the skill identifier, purpose, usage guidance, and entrypoint URI
- **AND** SHALL deliver the table as `user/information` content

#### Scenario: Resolve a nested skill
- **WHEN** an agent requests `guide://$workflow-status` through Guide's
  `read_resource` tool or a native MCP resource read
- **THEN** the system SHALL resolve the entrypoint below
  `{docroot}/_skills/workflow-status/SKILL.md`
- **AND** SHALL preserve the normal template suffix handling used by Guide commands
- **AND** SHALL make URI query parameters available to the skill template as
  `kwargs` and `raw_kwargs`, with a valueless key represented as `true`
- **AND** native resource-template transport SHALL preserve arbitrary skill
  query keywords before Guide applies that shared parsing

#### Scenario: Select a skill through the Guide prompt
- **WHEN** a caller supplies an argument beginning with `$` to the Guide prompt
- **THEN** the prompt SHALL route it through the same skill resolver as
  `read_resource`
- **AND** SHALL preserve path segments and query keyword semantics
- **AND** SHALL NOT treat the skill identifier as a category or collection

#### Scenario: Select a command through the Guide prompt
- **WHEN** a caller supplies an argument beginning with `_` to the Guide prompt
- **THEN** the prompt SHALL route it through the existing command dispatcher
- **AND** SHALL NOT treat the command identifier as a category or collection

### Requirement: Prompt project binding
The system SHALL require an active bound project for every Guide prompt before
the prompt router or task manager processes the request. A successful local
stdio PWD bootstrap MAY establish that binding first.

#### Scenario: Invoke a prompt without a project
- **WHEN** a client invokes any Guide prompt without an active project
- **THEN** the system SHALL return the standard `no_project` result
- **AND** SHALL NOT render prompt content, execute a command, or initialise
  task-manager work for that request

### Requirement: Codex skill-use proof
The system SHALL support validation that Codex can retrieve a selected Guide
skill and follow its instructions in a real task.

#### Scenario: Explicit skill use
- **WHEN** a user or agent explicitly selects a Guide skill
- **THEN** Codex retrieves its entrypoint through Guide before performing the
  governed task
- **AND** the validation records whether Codex followed the retrieved
  instructions

### Requirement: Workflow skill packages
The system SHALL serve Guide's five workflow phases as flat, verb-named skill
packages: `workflow-check`, `workflow-discuss`, `workflow-explore`,
`workflow-implement`, and `workflow-plan`. Each SHALL refer to the rendered
`workflow-file` template value when reading or updating workflow state.

#### Scenario: Render a workflow phase skill
- **WHEN** an agent selects one of the workflow phase skill packages
- **THEN** the rendered instructions SHALL use the configured workflow file
- **AND** the default workflow file SHALL be `.guide.yaml`
- **AND** the package name SHALL use the verb form rather than the workflow
  phase noun

### Requirement: Focused workflow status skill
The `workflow-status` skill SHALL report the configured workflow file without
changing the project. It SHALL not instruct the agent to inspect client
information, OpenSpec, Git state, task state, or handover data.

#### Scenario: Report workflow-file information when workflow mode is enabled
- **WHEN** an agent selects `guide://$workflow-status` while workflow mode is enabled
- **THEN** the skill SHALL instruct the agent to read the configured workflow
  file and report its workflow information
- **AND** it SHALL use `.guide.yaml` when no workflow-file override is set

#### Scenario: Report disabled workflow mode
- **WHEN** an agent selects `guide://$workflow-status` while workflow mode is disabled
- **THEN** the skill SHALL instruct the agent to report that workflow mode is disabled
- **AND** SHALL NOT name or inspect a workflow file

### Requirement: Frontmatter-declared skill input
The system SHALL let any Guide skill entrypoint declare named MCP forms in its
`elicitation` frontmatter. Each form SHALL declare a non-empty message and an
object schema with primitive properties. The shared resource resolver SHALL
request only forms whose required fields are absent from URI keywords, then
merge accepted declared fields into the skill's existing keyword template
context. Complete standard JSON Schema property defaults SHALL provide a safe
fallback when elicitation is unavailable or cancelled and SHALL identify the
defaulted form in the rendered template context. A form may instead declare
`fallback: render`, which SHALL render the entrypoint without unresolved form
values when elicitation is unavailable or cancelled. It SHALL not route forms
by skill identifier.

#### Scenario: Request a missing declared form
- **WHEN** an agent selects a skill entrypoint with a declared form whose
  required URI keywords are absent through either the native resource or the
  `read_resource` tool
- **THEN** Guide SHALL issue the same capability-negotiated MCP elicitation
  from either surface using that form's message and schema
- **AND** SHALL render the skill only after the user supplies valid values or
  after applying complete declared defaults following unavailable or cancelled
  elicitation
- **AND** SHALL retain explicit user declines rather than applying defaults
- **AND** when the form declares `fallback: render`, SHALL render the
  entrypoint without unresolved form values after unavailable or cancelled
  elicitation
- **AND** SHALL return clear required-keyword guidance only when unresolved
  required fields lack complete declared defaults

#### Scenario: Satisfy a declared form with URI keywords
- **WHEN** an agent selects a skill entrypoint with URI keywords satisfying a
  declared form's required fields
- **THEN** Guide SHALL render the skill without requesting that form
- **AND** SHALL preserve the URI keywords through the shared template keyword
  context

### Requirement: Workflow review skill
The system SHALL serve `workflow-review` as a packaged Guide skill for
independent code review. It SHALL transition the configured workflow file to
the review phase when workflow mode is active, and SHALL validate the active
OpenSpec change when OpenSpec mode is active.

#### Scenario: Choose a review target when mode is omitted
- **WHEN** an agent selects `guide://$workflow-review` without a `mode` query
  parameter through either the native resource or the `read_resource` tool
- **THEN** its declared `review-target` form SHALL offer mutually exclusive
  choices for uncommitted work, `main`, a named branch, and a pull request URL
  or number
- **AND** when that form is unavailable or cancelled, the skill SHALL direct
  the agent to present mutually exclusive
  client-native choices for uncommitted work, `main`, a named branch, and a
  pull request URL or number
- **AND** SHALL direct the agent to use the same choices as a numbered list
  when the client cannot render a choice picker
- **AND** SHALL direct the agent not to begin review until the user selects a
  target
- **AND** SHALL instruct it to read the configured workflow file before
  changing its phase to `review` when workflow mode is active

#### Scenario: Select a review target
- **WHEN** an agent selects `guide://$workflow-review` with `mode` equal to
  `uncommitted`, `main`, a branch name, a pull-request URL, or a pull-request
  number for the current repository
- **THEN** the skill SHALL direct it to review that selected target
- **AND** SHALL preserve the query value through the shared Guide template
  keyword context

#### Scenario: Obtain independent review coverage
- **WHEN** workflow review begins
- **THEN** the skill SHALL direct the agent to obtain two independent reviews
- **AND** one SHALL use the heavier available model at medium or high effort
- **AND** the other SHALL use a different lighter available model at its
  highest supported effort when possible
- **AND** they SHALL run concurrently in isolated subprocesses when that
  execution mechanism is supported
- **AND** each reviewer SHALL receive only the selected target, relevant
  repository evidence, governing repository guidance, applicable OpenSpec
  artefacts, and the required report format
- **AND** neither reviewer SHALL receive or account for prior conversation,
  previous reviews, existing review records, collated inventories, or the
  other reviewer's findings
- **AND** the agent SHALL deduplicate and collate only the reports produced by
  this review before user
  triage

#### Scenario: Account for existing pull-request comments after independent review
- **WHEN** the selected target is a pull request with existing review comments
- **THEN** the coordinator SHALL inspect those comments only after the fresh
  independent reviews have completed
- **AND** SHALL annotate matching combined findings as already flagged or add
  useful context to them
- **AND** SHALL NOT expose those comments to the independent reviewers or
  modify their source reports

#### Scenario: Validate the active OpenSpec change
- **WHEN** OpenSpec mode is active for a workflow review
- **THEN** the skill SHALL direct the agent to run strict validation for the
  active change before completing the review

### Requirement: Just-one finding triage skill
The system SHALL serve `just-one` as a packaged Guide skill for finding
triage. It SHALL collect the user's decision for every finding in the shared
review record before applying any accepted work.

#### Scenario: Present a finding
- **WHEN** the agent begins `just-one` triage with a fixed inventory of
  findings
- **THEN** it SHALL present exactly one finding at a time
- **AND** each presentation SHALL include its fixed `current/total` position,
  P1-to-P6 priority, short description, analysis, and recommendation

#### Scenario: Record a decision without editing
- **WHEN** the user accepts, declines, discusses, or varies the current
  finding
- **THEN** the agent SHALL record the resulting disposition in the originating
  review JSON record
- **AND** SHALL NOT implement an accepted action while any finding remains
  undecided

#### Scenario: Confirm collected actions
- **WHEN** every finding has a recorded disposition
- **THEN** the agent SHALL show the accepted action list
- **AND** SHALL request explicit user confirmation before applying it
- **AND** SHALL implement only the actions confirmed by the user

### Requirement: Durable review finding records
The workflow review skill SHALL record each independent review in
`{{path.documents}}Reviews/<issue>/<agent-name>.json`, and SHALL write its
combined inventory to `{{path.documents}}Reviews/<issue>.json`. The workflow
file's required `issue` field SHALL name both paths. An empty value means there
is no active workflow issue; the agent SHALL report that state and SHALL NOT
dispatch a review or begin triage. Each source record SHALL identify its
reviewer, version, and review target, and each finding SHALL carry a stable
identifier, version, P1-to-P6 priority, location, description, analysis, and
recommendation. The combined inventory SHALL retain references to the source
findings and their versions, and SHALL be the only review record triage updates
with the user's decision, variation, rationale, action, and completion state.

#### Scenario: Record independent reviews
- **WHEN** workflow review obtains independent reviewer outputs
- **THEN** each reviewer SHALL write its own JSON record below the shared
  review directory
- **AND** before dispatch the coordinator SHALL determine each reviewer's next
  positive version without exposing its earlier findings
- **AND** a reviewer SHALL overwrite only its own prior record and SHALL assign
  its current version to every finding it writes
- **AND** one reviewer SHALL NOT overwrite another reviewer's record
- **AND** a reviewer SHALL NOT load, merge, or update adjacent review records
  while producing its own report
- **AND** the coordinator SHALL write only the reports produced for the current
  review into the canonical combined inventory

#### Scenario: Record triage without implementation
- **WHEN** the user decides a finding during `just-one` triage
- **THEN** the agent SHALL update the corresponding finding in the canonical
  combined JSON inventory with that
  decision and any variation or implementation guidance
- **AND** SHALL NOT implement the finding while any finding remains undecided

### Requirement: Experimental MCP skills extension
The system SHALL support the opt-in, non-standard
`io.uniquode/mcp-guide-skills` MCP extension for Guide skills. The
extension SHALL provide `skills/list` and
`notifications/skills/list_changed` to a client that has negotiated support
for it. The extension SHALL not be required for access to the Guide skill
catalogue or skill resources.

#### Scenario: Enable the global experiment
- **WHEN** the global `mcp-skills` feature flag is true at Guide startup
- **THEN** the server SHALL advertise the namespaced skills extension during
  MCP capability negotiation
- **AND** the capability set SHALL remain stable for the lifetime of that
  server process

#### Scenario: Leave the experiment disabled
- **WHEN** `mcp-skills` is absent or false at Guide startup
- **THEN** the server SHALL not advertise the skills extension
- **AND** SHALL NOT serve `skills/list` or emit
  `notifications/skills/list_changed`
- **AND** existing Guide skill catalogue and resource access SHALL remain
  available

#### Scenario: Reject project-scoped configuration
- **WHEN** a project configuration attempts to set `mcp-skills`
- **THEN** Guide SHALL reject the project-level flag as invalid

#### Scenario: List effective skills through the extension
- **WHEN** a client that negotiated the skills extension requests
  `skills/list` for an active bound Guide session while `mcp-skills` is enabled
- **THEN** the system SHALL return only the skills effective for that session
- **AND** the request SHALL require that session's opaque Guide `session_id`
- **AND** the result SHALL contain a `skills` array
- **AND** each listed skill SHALL identify its stable identifier, metadata, and
  retrieval URI

#### Scenario: Reject an unnegotiated skills request
- **WHEN** a client that did not negotiate the skills extension requests
  `skills/list`
- **THEN** the system SHALL reject the request as requiring the skills
  extension
- **AND** SHALL NOT treat the request as access to the ordinary Guide skill
  catalogue

#### Scenario: Refresh a negotiated client after availability changes
- **WHEN** a change to an active session's binding, effective feature flags, or
  discoverable skill packages changes its effective skills while `mcp-skills`
  is enabled
- **THEN** the system SHALL send
  `notifications/skills/list_changed` to that negotiated client
- **AND** the notification SHALL carry no payload
- **AND** the client SHALL be able to refresh by calling `skills/list`
- **AND** when no request context for that same client is active, the system
  SHALL retain the changed list until that client's next request
- **AND** the system SHALL update its delivered-list snapshot only after the
  notification is sent to that same client

#### Scenario: Preserve negotiated skills across a project switch
- **WHEN** a negotiated client has called `skills/list` and then switches its
  active bound project
- **THEN** Guide SHALL retain the negotiated skills subscription and last
  effective skills list on the replacement active Session
- **AND** SHALL evaluate the replacement Session's effective skills for a
  list-change notification
- **AND** SHALL NOT transfer project-local task, rendering, or instruction
  state from the expiring Session

#### Scenario: Transfer interaction-scoped protocol subscriptions
- **WHEN** a Session is replaced after a project switch
- **THEN** Guide SHALL transfer only listeners explicitly declared as
  interaction-scoped to the replacement Session
- **AND** SHALL invoke their declared replacement lifecycle callback
- **AND** SHALL recreate or retain session-scoped listeners only with the
  Session that owns them

#### Scenario: Avoid irrelevant skills refreshes
- **WHEN** a configuration or package change does not alter an active
  negotiated session's effective skills
- **THEN** the system SHALL NOT send
  `notifications/skills/list_changed` for that session
