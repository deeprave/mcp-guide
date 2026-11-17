# Spec Delta

## ADDED Requirements

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
resource reads.
Because Guide renders packages for the current interaction, entries SHALL
declare dynamically generated resources rather than a static integrity manifest.

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
- **WHEN** a template renders `{{#skill}}git-commit{{/skill}}`
- **THEN** the section SHALL render `skill://git-commit/SKILL.md`

#### Scenario: Resolve a compatibility skill reference
- **WHEN** a client supplies a `skill://` URI to Guide's `read_resource`
- **THEN** Guide SHALL resolve it through the standard skill resource resolver

### Requirement: Workflow review depth
The workflow-review skill and its paired command SHALL accept a `depth`
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
directory. Bound workflow reviews SHALL use the Guide project identity and
active issue as their key. Unbound pull-request reviews and triage SHALL use
canonical provider, immutable repository identity, and pull-request number.
Guide SHALL NOT require explicit user configuration to access that directory.

#### Scenario: Cache path is available in every rendering context
- **WHEN** Guide renders a skill before or after project binding
- **THEN** `path.cache` SHALL identify the Guide user-cache directory
- **AND** that directory SHALL be an implied runtime read/write location

#### Scenario: Unbound pull-request review has a stable cache record
- **WHEN** an unbound workflow review targets a pull request
- **THEN** Guide SHALL store its combined record at `path.cache/reviews/<provider>/<repository-id>/<pr-number>.json`

#### Scenario: Existing project review artefacts are not migrated
- **WHEN** Guide begins using the shared review cache
- **THEN** it SHALL NOT migrate existing project review or triage documents into that cache

### Requirement: Unbound triage skills
Guide SHALL provide unbound variants of triage-items, triage-review, and
triage-pr. The unbound variants SHALL use explicit user-supplied inventories,
review inputs, or pull-request identity rather than project workflow state or
project document paths.

#### Scenario: Triage items without a project
- **WHEN** an unbound user supplies an inventory for triage-items
- **THEN** Guide SHALL present its items one at a time
- **AND** SHALL retain decisions in the conversation unless the user requests an output destination

#### Scenario: Triage pull-request feedback without a project
- **WHEN** an unbound user invokes triage-pr with an explicit pull-request identity
- **THEN** Guide SHALL use the canonical pull-request cache record to identify new feedback
- **AND** SHALL not infer project workflow state or a project document path

#### Scenario: Later triage finds new review threads
- **WHEN** triage-pr revisits a pull request with existing triage state
- **THEN** Guide SHALL identify review threads not represented by that state
- **AND** SHALL retain the earlier thread state

#### Scenario: Bound and unbound triage share a pull request
- **WHEN** a pull request is triaged first while unbound and later while bound
- **THEN** the later triage SHALL use the same pull-request state

## REMOVED Requirements

### Requirement: Experimental MCP skills extension
**Reason**: The private `io.uniquode/mcp-guide-skills` identifier and opaque
session parameter are superseded by the standard MCP skills extension.

**Migration**: Clients SHALL negotiate `io.modelcontextprotocol/skills`, use
`skills/list` without a Guide session identifier, and retrieve entries through
`skills/get` or their `skill://` resources. Guide retains its existing refresh
notification and its `guide://$`, `list_skills`, and `use_skill` surfaces.
