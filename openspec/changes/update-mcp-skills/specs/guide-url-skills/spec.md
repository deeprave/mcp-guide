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

### Requirement: Project-aware standard skill availability
The standard skills catalogue SHALL be available before project binding.
Packages SHALL declare `allow-unbound: true` to be available unbound;
omitting the field or declaring it false SHALL require a bound project. Guide
SHALL apply ordinary frontmatter requirements only after binding.

#### Scenario: List unbound-safe skills
- **WHEN** an unbound client requests `skills/list`
- **THEN** Guide SHALL return only packages that declare
  `allow-unbound: true`
- **AND** SHALL not require an opaque Guide `session_id`

#### Scenario: Expand the catalogue after binding
- **WHEN** the same client binds a project and requests `skills/list` again
- **THEN** Guide SHALL include project-dependent packages whose frontmatter
  requirements are satisfied by that project
- **AND** SHALL continue to include available unbound-safe packages

#### Scenario: Notify after binding expands availability
- **WHEN** a session binding or effective skill availability changes
- **THEN** Guide SHALL make the updated catalogue available to the next
  `skills/list` request
- **AND** after binding, SHALL emit `notifications/skills/list_changed` to a
  client that negotiated the skills extension

### Requirement: Safe unbound skill rendering
An `allow-unbound: true` package SHALL render complete guidance without a
project path, configured policy, workflow state, or project-scoped storage
location. A package MAY add project-specific guidance only when a project is
bound.

#### Scenario: Render an unbound Git skill
- **WHEN** an unbound client retrieves an eligible Git skill
- **THEN** Guide SHALL render its generic Git delivery guidance
- **AND** SHALL omit selected policy, tracker, and project-delivery directives

#### Scenario: Render an eligible skill after binding
- **WHEN** a bound client retrieves an `allow-unbound: true` package
- **THEN** Guide SHALL render its project-specific guidance when applicable

### Requirement: Standard skill resource delivery
Each skill in the standard catalogue SHALL use a stable `skill://` entrypoint
URI and SHALL be retrievable through `skills/get` and MCP resource reads.
Because Guide renders packages for the current interaction, entries SHALL
declare dynamically generated resources rather than a static integrity manifest.

#### Scenario: List standard skill metadata
- **WHEN** an eligible skill is returned by `skills/list`
- **THEN** its entry SHALL conform to the standard skills schema
- **AND** SHALL include its public name, description, `skill://` `SKILL.md`
  URI, frontmatter, and dynamic-resources declaration

#### Scenario: Retrieve a listed skill
- **WHEN** a client requests a listed skill's `SKILL.md` URI through
  `skills/get` or `resources/read`
- **THEN** Guide SHALL return the rendered entrypoint for that interaction
- **AND** a package member URI below the same `skill://` package root SHALL
  resolve using the same rendering and containment rules as `guide://$`

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

### Requirement: Capability-aware skill template references
The `skill` template section SHALL render a canonical skill entrypoint
reference for the current client. Standard references SHALL identify
`SKILL.md`; Guide fallback references SHALL retain the `guide://$` scheme.

#### Scenario: Render a negotiated skill reference
- **WHEN** a template renders `{{#skill}}git-commit{{/skill}}` for a client
  that negotiated the Skills extension
- **THEN** the section SHALL render `skill://git-commit/SKILL.md`

#### Scenario: Render a compatibility skill reference
- **WHEN** a template renders a skill reference for a legacy or non-negotiating
  client
- **THEN** the section SHALL render the corresponding `guide://$` URI

## REMOVED Requirements

### Requirement: Experimental MCP skills extension
**Reason**: The private `io.uniquode/mcp-guide-skills` identifier and opaque
session parameter are superseded by the standard MCP skills extension.

**Migration**: Clients SHALL negotiate `io.modelcontextprotocol/skills`, use
`skills/list` without a Guide session identifier, and retrieve entries through
`skills/get` or their `skill://` resources. Guide retains its existing refresh
notification and its `guide://$`, `list_skills`, and `use_skill` surfaces.
