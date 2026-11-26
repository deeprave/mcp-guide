# guide-url-skills Specification

## Purpose
Define Guide's server-owned, package-shaped skills: discovery, explicit
`guide://$` retrieval, skill inputs, workflow skills, durable review records,
and the opt-in negotiated MCP skills extension.

## Requirements

### Requirement: Packaged Guide skill serving
The system SHALL serve reusable Guide skills as package-shaped resources rooted
at `SKILL.md` through Guide resources for explicit selection by an agent.

#### Scenario: Serve a skill package entrypoint
- **WHEN** an agent requests a supported named skill for the current project
- **THEN** the system SHALL render that package's `SKILL.md` entrypoint through Guide
- **AND** the content SHALL be rendered for the current project and Guide
  settings
- **AND** the response `message` SHALL identify the rendered virtual path, such as
  `guide-status/SKILL.md`
- **AND** the response `value` SHALL contain the rendered entrypoint content

### Requirement: Guide skill catalogue tool registration

Guide SHALL expose the packaged-skill catalogue through the standard
`list_skills` tool registration pattern.

#### Scenario: Catalogue tool registration
- **WHEN** an agent lists skills through the Guide tool surface
- **THEN** the standard list_skills registration provides the skill catalogue

### Requirement: Reserved Guide skill namespaces

Category and collection names SHALL reserve leading `_`, `$`, and `!`
characters for internal namespaces.

#### Scenario: Reserved namespace name
- **WHEN** a category or collection name starts with an internal namespace prefix
- **THEN** Guide treats that prefix as reserved

#### Scenario: Serve a package member
- **WHEN** an agent requests a member below an available package, such as
  `guide://$guide-status/resources/checklist.md`
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

The system SHALL provide a minimal Guide skill catalogue containing the metadata needed for an agent to explicitly select a skill.

#### Scenario: Inspect available skills
- **WHEN** an agent requests the catalogue through `list_skills` or `guide://$` through Guide's `read_resource` tool
- **THEN** the system SHALL list each available skill's identifier, description, and usage guidance from its frontmatter
- **AND** SHALL identify the resource URI for the skill entrypoint
- **AND** SHALL deliver the catalogue as `agent/information` content by default

#### Scenario: Isolate an invalid skill package
- **WHEN** one discovered skill package is unreadable, malformed, or has an invalid package identifier or public `name` value
- **THEN** the system SHALL log and exclude that package
- **AND** SHALL continue to return every independently valid skill package

#### Scenario: Use URI-safe skill identities
- **WHEN** Guide discovers a skill package
- **THEN** its package identifier and public `name` frontmatter value SHALL satisfy the shared category and collection name validation contract
- **AND** SHALL be safe to advertise and resolve in a `guide://$` URI without additional encoding

#### Scenario: Display available skills
- **WHEN** a caller requests `list_skills` with `verbose=true`
- **THEN** the system SHALL list the same available-skill catalogue
- **AND** SHALL deliver it as `user/information` content

#### Scenario: Display skills through a resource URI
- **WHEN** a caller requests `guide://$?verbose`
- **THEN** the system SHALL forward the URI query parameters to the skill catalogue loader
- **AND** SHALL deliver the catalogue as `user/information` content

#### Scenario: Display skills as a table
- **WHEN** a caller requests `list_skills(table=true)` or `guide://$?table`
- **THEN** the system SHALL return the available skills as a Markdown table
- **AND** each row SHALL contain the skill identifier, purpose, usage guidance, and entrypoint URI
- **AND** SHALL deliver the table as `user/information` content

#### Scenario: Resolve a nested skill
- **WHEN** an agent requests `guide://$guide-status` through Guide's `read_resource` tool or a native MCP resource read
- **THEN** the system SHALL resolve the entrypoint below `{docroot}/_skills/guide/status/SKILL.md`
- **AND** SHALL preserve the normal template suffix handling used by Guide commands
- **AND** SHALL make URI query parameters available to the skill template as `kwargs`, with a valueless key represented as `true`
- **AND** native resource-template transport SHALL preserve arbitrary skill query keywords before Guide applies that shared parsing

#### Scenario: Select a skill through the Guide prompt
- **WHEN** a caller supplies an argument beginning with `$` to the Guide prompt
- **THEN** the prompt SHALL route it through the same skill resolver as `read_resource`
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

### Requirement: Frontmatter-declared skill input

The system SHALL let any Guide skill entrypoint declare named MCP forms in its
`elicitation` frontmatter. Each form SHALL declare a non-empty message and an
object schema with primitive properties.

#### Scenario: Declared form schema
- **WHEN** a skill declares an elicitation form
- **THEN** the form has a non-empty message and an object schema with primitive properties

### Requirement: Missing-field skill form resolution

The shared resource resolver SHALL request only forms whose required fields are
absent from URI keywords, then merge accepted declared fields into the skill's
existing keyword template context.

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

### Requirement: Skill form default fallback

Complete standard JSON Schema property defaults SHALL provide a fallback when
elicitation is unavailable or cancelled and SHALL identify the defaulted form in
the rendered template context.

#### Scenario: Unavailable form uses complete defaults
- **WHEN** a declared form is unavailable or cancelled and has complete property defaults
- **THEN** Guide applies the defaults and identifies the defaulted form in template context

### Requirement: Skill form rendering fallback

A form declaring `fallback: render` SHALL render the entrypoint without
unresolved form values when elicitation is unavailable or cancelled.

#### Scenario: Render fallback after unavailable elicitation
- **WHEN** a fallback-render form is unavailable or cancelled
- **THEN** Guide renders its entrypoint without unresolved form values

### Requirement: Skill form routing independence

Guide SHALL not route a declared form by skill identifier.

#### Scenario: Form routing
- **WHEN** Guide resolves a declared skill form
- **THEN** its routing does not depend on the skill identifier

#### Scenario: Satisfy a declared form with URI keywords
- **WHEN** an agent selects a skill entrypoint with URI keywords satisfying a
  declared form's required fields
- **THEN** Guide SHALL render the skill without requesting that form
- **AND** SHALL preserve the URI keywords through the shared template keyword
  context

### Requirement: Standard MCP skills extension
For modern-protocol clients, the system SHALL advertise
`io.modelcontextprotocol/skills` and serve the SEP-2640 `skills/list` and
`skills/get` operations. Its capability set SHALL remain stable for the server
process lifetime.

#### Scenario: Negotiate standard skills delivery
- **WHEN** a modern client negotiates the Skills extension
- **THEN** Guide SHALL advertise `io.modelcontextprotocol/skills` during MCP
  capability negotiation
- **AND** SHALL make `skills/list` and `skills/get` available to a negotiated
  client

#### Scenario: Retain legacy skills delivery
- **WHEN** a client is legacy or does not negotiate the Skills extension
- **THEN** Guide SHALL not require the client to use the standard skills methods
- **AND** `guide://$`, `list_skills`, and `use_skill` SHALL remain available

### Requirement: Unbound standard skill availability
The standard skills catalogue SHALL be available before project binding.
Packages requiring no context or only project binding SHALL be discoverable
before binding. A package requiring project binding SHALL identify that in its
description and direct the agent to `{{tool_prefix}}set_project`. A package
with requirements beyond project binding SHALL remain unavailable from the
standard unbound catalogue.

#### Scenario: List skills before binding
- **WHEN** an unbound client requests `skills/list`
- **THEN** Guide SHALL return packages requiring no context or only project
  binding
- **AND** SHALL omit packages with additional unmet requirements
- **AND** SHALL not require an opaque Guide `session_id`

#### Scenario: Inspect skill metadata without rendering
- **WHEN** Guide builds a standard or compatibility skill catalogue
- **THEN** it SHALL inspect package frontmatter only
- **AND** SHALL NOT render a skill template, load a partial, or resolve policy
  content during catalogue construction

### Requirement: Binding-only skill metadata
`project-bind: true` SHALL declare a package's project-binding prerequisite.
It SHALL be catalogue metadata rather than a project feature flag or a
`requires-*` condition.

#### Scenario: Discover a binding-only package
- **WHEN** an unbound client lists a package declaring `project-bind: true`
- **AND** that package has no additional unmet requirements
- **THEN** Guide SHALL include it in the catalogue with binding guidance

#### Scenario: Retain an unbound standard catalogue after binding
- **WHEN** a client binds a project and requests `skills/list`
- **THEN** Guide SHALL continue to return the unbound metadata catalogue
- **AND** SHALL NOT require the opaque Guide `session_id`
- **AND** a known `skill://` resource read with that identifier SHALL use the
  bound session for rendering

#### Scenario: Notify after a catalogue change
- **WHEN** rebuilding detects an effective skill catalogue change
- **THEN** Guide SHALL make the updated catalogue available to the next
  `skills/list` request
- **AND** SHALL emit `notifications/skills/list_changed` to the requesting
  client when it negotiated the skills extension

### Requirement: Safe unbound skill rendering
A package available without binding SHALL render complete project-independent
guidance without a project path, configured policy, workflow state, or
project-scoped storage location. A package requiring project binding SHALL
return the shared no-project result until a project is bound. A package MAY add
project-specific guidance only when a project is bound.

#### Scenario: Render an unbound Git skill
- **WHEN** an unbound client retrieves an eligible Git skill
- **THEN** Guide SHALL render its generic Git delivery guidance
- **AND** SHALL omit selected policy, tracker, and project-delivery directives

#### Scenario: Resolve policies for a selected skill
- **WHEN** Guide renders a selected skill for an unbound interaction
- **THEN** its policy partials SHALL resolve to blank content without requiring
  project policy resolution
- **WHEN** Guide renders a selected skill for a bound interaction
- **THEN** it SHALL resolve that project's selected policy partials through the
  shared rendering path

#### Scenario: Render an eligible skill after binding
- **WHEN** a bound client retrieves a package available before binding
- **THEN** Guide SHALL render its project-specific guidance when applicable

#### Scenario: Render a binding-required skill before binding
- **WHEN** an unbound client retrieves a package requiring project binding
- **THEN** Guide SHALL return the shared no-project result
- **AND** SHALL NOT render project-dependent package content

### Requirement: Standard skill resource delivery
Each skill in the standard catalogue SHALL use a stable `skill://` entrypoint
URI and SHALL be described through `skills/get` and rendered through MCP
resource reads. Because Guide renders packages for the current interaction,
entries SHALL declare dynamically generated resources rather than a static
integrity manifest.

#### Scenario: List standard skill metadata
- **WHEN** an eligible skill is returned by `skills/list`
- **THEN** its entry SHALL conform to the standard skills schema
- **AND** SHALL include its public name, description, `skill://` `SKILL.md`
  URI, frontmatter, and dynamic-resources declaration

#### Scenario: Retrieve a listed skill
- **WHEN** a client requests a listed skill through `skills/get`
- **THEN** Guide SHALL return its current metadata without rendering its
  entrypoint
- **WHEN** a client reads that skill's `SKILL.md` URI through `resources/read`
- **THEN** Guide SHALL render the entrypoint for that interaction using the
  same selected-skill resolver as `guide://$`
- **AND** a package member URI below the same `skill://` package root SHALL
  resolve using the same rendering and containment rules as `guide://$`

#### Scenario: Read a bound skill through stateless transport
- **WHEN** a client that received a Guide `session_id` reads a known
  `skill://` resource with that value as its `session_id` query argument
- **THEN** Guide SHALL resolve the bound session for the resource read
- **AND** SHALL retain the canonical session-free URI in `skills/list`

#### Scenario: Reject an unavailable standard skill
- **WHEN** an unbound or bound client requests a standard skill URI that is not
  in its effective catalogue
- **THEN** Guide SHALL reject the request as unavailable
- **AND** SHALL not expose package content solely because the client supplied
  its URI

#### Scenario: Do not expose a template directory tree
- **WHEN** a client negotiates standard skill delivery
- **THEN** Guide SHALL NOT advertise or implement
  `resources/directory/read`
- **AND** SHALL NOT derive a public skill-resource inventory by walking the
  package template filesystem

### Requirement: Canonical skill template references
The `skill` template section SHALL render a canonical `skill://` entrypoint
reference identifying `SKILL.md`. Guide's `read_resource` compatibility
surface SHALL resolve that URI.

#### Scenario: Render a skill reference
- **WHEN** a template renders `{{#skill}}guide-git-commit{{/skill}}`
- **THEN** the section SHALL render `skill://guide-git-commit/SKILL.md`

#### Scenario: Resolve a compatibility skill reference
- **WHEN** a client supplies a `skill://` URI to Guide's `read_resource`
- **THEN** Guide SHALL resolve it through the standard skill resource resolver

### Requirement: Workflow review depth
The guide-review skill and its paired command SHALL accept a `depth`
selection. `quick` SHALL run one lighter reviewer, `standard` SHALL run one
heavier reviewer, and `thorough` SHALL run both independently. `thorough`
SHALL be the default. The orchestrating agent SHALL return one combined review
after all selected reviews complete.

#### Scenario: Quick workflow review
- **WHEN** a workflow review is requested with `depth` set to `quick`
- **THEN** Guide SHALL instruct one lighter reviewer to review the selected target
- **AND** SHALL return that review as the combined result

#### Scenario: Standard workflow review
- **WHEN** a workflow review is requested with `depth` set to `standard`
- **THEN** Guide SHALL instruct one heavier reviewer to review the selected target
- **AND** SHALL return that review as the combined result

#### Scenario: Thorough workflow review
- **WHEN** a workflow review is requested without `depth` or with it set to `thorough`
- **THEN** Guide SHALL instruct one lighter and one heavier reviewer to review the selected target independently
- **AND** the orchestrating agent SHALL return one combined review after both complete

### Requirement: Shared review cache
Guide SHALL retain review and pull-request triage records in its user-cache
directory. Bound review triage SHALL use the Guide project identity and active
issue as its key. Unbound pull-request triage SHALL use canonical provider,
immutable repository identity, and pull-request number.
Guide SHALL NOT require explicit user configuration to access that directory.

#### Scenario: Cache path is available in every rendering context
- **WHEN** Guide renders a skill before or after project binding
- **THEN** `path.cache` SHALL identify the Guide user-cache directory
- **AND** that directory SHALL be an implied runtime read/write location

#### Scenario: Bound triage has one canonical issue record
- **WHEN** Guide collates review evidence for a bound workflow issue
- **THEN** it SHALL retain the canonical findings record at
  `path.cache/reviews/<project-hash>/<issue>.json`
- **AND** it SHALL retain references to independent agent, external-review, and
  pull-request sources rather than replacing their evidence

#### Scenario: Link a pull request to bound issue evidence by branch
- **WHEN** a bound guide-triage request has a pull request whose head branch
  matches the current local branch
- **THEN** Guide SHALL associate its evidence with the active issue's canonical
  findings record
- **AND** otherwise SHALL triage that pull request without reading or updating
  the active issue's records

#### Scenario: Unbound pull-request review has a stable cache record
- **WHEN** an unbound guide-triage request targets a pull request
- **THEN** Guide SHALL store its combined record at `path.cache/reviews/<provider>/<repository-id>/<pr-number>.json`

#### Scenario: Existing project review artefacts are not migrated
- **WHEN** Guide begins using the shared review cache
- **THEN** it SHALL NOT migrate existing project review or triage documents into that cache

### Requirement: Unbound triage skills
Guide SHALL provide unbound variants of guide-triage and guide-sequence. The
unbound variants SHALL use explicit user-supplied inventories, review inputs,
or pull-request identity rather than project workflow state or project document
paths.

#### Scenario: Triage items without a project
- **WHEN** an unbound user supplies an inventory for guide-sequence
- **THEN** Guide SHALL present its items one at a time
- **AND** SHALL retain decisions in the conversation unless the user requests an output destination

#### Scenario: Triage pull-request feedback without a project
- **WHEN** an unbound user invokes guide-triage with an explicit pull-request identity
- **THEN** Guide SHALL use the canonical pull-request cache record to identify new feedback
- **AND** SHALL not infer project workflow state or a project document path

#### Scenario: Later triage finds new review threads
- **WHEN** guide-triage revisits a pull request with existing triage state
- **THEN** Guide SHALL identify review threads not represented by that state
- **AND** SHALL retain the earlier thread state

#### Scenario: Bound and unbound triage share a pull request
- **WHEN** a pull request is triaged first while unbound and later while bound
- **THEN** the later triage SHALL use the same pull-request state

### Requirement: Tool facade invokes a Guide skill through shared resolution
The system SHALL expose `{{tool_prefix}}use_skill` as a project-dependent MCP
tool registered through `@toolfunc`.

#### Scenario: Tool is called without a project
- **WHEN** an unbound client calls `{{tool_prefix}}use_skill`
- **THEN** it receives the standard no-project result used by other
  project-dependent tools

### Requirement: Tool-facade skill identifier input

The first `{{tool_prefix}}use_skill` argument SHALL be a plain Guide skill name,
with or without a leading `$`, and SHALL NOT be a URI. The tool SHALL resolve
only an exact effective skill identifier.

#### Scenario: Tool rejects a skill member path
- **WHEN** a client calls `{{tool_prefix}}use_skill` with a skill member path
- **THEN** it receives the ordinary no-such-skill result

#### Scenario: Tool accepts the optional skill marker
- **WHEN** a bound client calls `{{tool_prefix}}use_skill` for
  `$guide-review`
- **THEN** it resolves the `guide-review` Guide skill

### Requirement: Tool-facade skill argument parsing

The optional `{{tool_prefix}}use_skill` `args` list SHALL use the shared Guide
command-argument parser, with the skill name as argv[0].

#### Scenario: Tool invokes a skill with arguments
- **WHEN** a bound client calls `{{tool_prefix}}use_skill` for
  `guide-review` with `args: ["mode=uncommitted", "verbose"]`
- **THEN** the resolved skill receives `mode` with value `uncommitted` and
  `verbose` with value `true` through its keyword template context
- **AND** the tool uses the shared command-argument parser rather than duplicating it

### Requirement: Tool-facade shared skill resolution

The MCP tool layer SHALL NOT duplicate the skill's argument, elicitation,
policy, rendering, or response-handling behaviour.

#### Scenario: Tool delegates skill resolution
- **WHEN** a bound client invokes a resolved Guide skill through the tool facade
- **THEN** shared skill resolution handles its arguments, elicitation, policy, rendering, and response behaviour

### Requirement: Contextual Guide triage
Guide SHALL provide `guide-triage` to collect and collate review evidence. It
SHALL use explicit user-supplied review material in preference to contextual
sources, and SHALL otherwise use applicable bound issue or pull-request context.

#### Scenario: Triage supplied review material
- **WHEN** a user invokes `guide-triage` with a review file or directory
- **THEN** Guide SHALL use that material rather than infer a workflow issue or
  pull request

#### Scenario: Triage a bound review issue
- **WHEN** a bound user invokes `guide-triage` without explicit review material
- **AND** the active workflow identifies an issue
- **THEN** Guide SHALL collate the issue's independent review reports into its
  canonical findings record

#### Scenario: Triage pull-request feedback
- **WHEN** guide-triage has an applicable pull request
- **THEN** Guide SHALL collate its review threads, summaries, and review-related
  comments with other relevant evidence
- **AND** SHALL preserve source and location references when deduplicating a concern

### Requirement: Sequential Guide decisions
Guide SHALL provide `guide-sequence` to present a stable item inventory in a
user-selected order. It SHALL present only the current item and its sequence
position, title, description, and applicable optional priority, analysis, and
recommendation fields. Its decisions SHALL be conversational.

#### Scenario: Decide a review finding
- **WHEN** guide-sequence presents a review finding
- **THEN** it SHALL accept Accept, Decline, Next, Skip, Vary, and Defer as
  decisions for the current item
- **AND** Accept or Vary SHALL record a follow-up without executing it
- **AND** Defer SHALL record a context todo

#### Scenario: Decide a non-review item
- **WHEN** guide-sequence presents a non-review item
- **THEN** it SHALL accept Ok or an Action supplied by the user

#### Scenario: Use an exported sequential skill
- **WHEN** an exported guide-sequence skill receives an explicit stable inventory
- **THEN** it SHALL guide the same conversational walkthrough without requiring
  Guide runtime state or MCP elicitation support

### Requirement: Guide commands remain independent from skill identities
Guide command URIs and command-template locations SHALL remain unchanged when
the selected skill package identities and locations change. References from a
command to a selected skill SHALL use that skill's new public name.

#### Scenario: Invoke an unchanged workflow command
- **WHEN** an agent reads `guide://_workflow/review`
- **THEN** Guide SHALL resolve the existing workflow review command
- **AND** SHALL NOT require the former or current public skill name in the URI
