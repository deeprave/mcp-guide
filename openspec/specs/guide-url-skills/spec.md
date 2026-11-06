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
  `workflow-status/SKILL.md`
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
  `$workflow-review`
- **THEN** it resolves the `workflow-review` Guide skill

### Requirement: Tool-facade skill argument parsing

The optional `{{tool_prefix}}use_skill` `args` list SHALL use the shared Guide
command-argument parser, with the skill name as argv[0].

#### Scenario: Tool invokes a skill with arguments
- **WHEN** a bound client calls `{{tool_prefix}}use_skill` for
  `workflow-review` with `args: ["mode=uncommitted", "verbose"]`
- **THEN** the resolved skill receives `mode` with value `uncommitted` and
  `verbose` with value `true` through its keyword template context
- **AND** the tool uses the shared command-argument parser rather than duplicating it

### Requirement: Tool-facade shared skill resolution

The MCP tool layer SHALL NOT duplicate the skill's argument, elicitation,
policy, rendering, or response-handling behaviour.

#### Scenario: Tool delegates skill resolution
- **WHEN** a bound client invokes a resolved Guide skill through the tool facade
- **THEN** shared skill resolution handles its arguments, elicitation, policy, rendering, and response behaviour
