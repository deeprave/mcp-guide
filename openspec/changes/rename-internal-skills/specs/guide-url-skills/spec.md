# Spec Delta

## MODIFIED Requirements

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
- **THEN** the system SHALL resolve the entrypoint below `{docroot}/_skills/workflow/status/SKILL.md`
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

### Requirement: Shared review cache
Guide SHALL retain review and pull-request triage records in its user-cache
directory. Bound review triage SHALL use the Guide project identity and active
issue as their key. Unbound pull-request triage SHALL use canonical provider,
immutable repository identity, and pull-request number. Guide SHALL NOT
require explicit user configuration to access that directory.

#### Scenario: Cache path is available in every rendering context
- **WHEN** Guide renders a skill before or after project binding
- **THEN** `path.cache` SHALL identify the Guide user-cache directory
- **AND** that directory SHALL be an implied runtime read/write location

#### Scenario: Bound triage has one canonical issue record
- **WHEN** Guide collates review evidence for a bound workflow issue
- **THEN** it SHALL retain the canonical findings record at
  `path.cache/reviews/<project-hash>/<issue>/review-findings.json`
- **AND** it SHALL retain references to independent agent, external-review, and
  pull-request sources rather than replacing their evidence

#### Scenario: Unbound pull-request review has a stable cache record
- **WHEN** an unbound guide-triage request targets a pull request
- **THEN** Guide SHALL store its combined record at
  `path.cache/reviews/<provider>/<repository-id>/<pr-number>.json`

#### Scenario: Existing project review artefacts are not migrated
- **WHEN** Guide begins using the shared review cache
- **THEN** it SHALL NOT migrate existing project review or triage documents into that cache

### Requirement: Unbound triage skills
Guide SHALL provide unbound variants of guide-triage and guide-sequence. The
unbound variants SHALL use explicit user-supplied inventories, review inputs,
or pull-request identity rather than project workflow state or project
document paths.

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

## ADDED Requirements

### Requirement: Contextual Guide triage
Guide SHALL provide `guide-triage` to collect and collate review evidence. It
SHALL use explicit user-supplied review material in preference to contextual
sources, and SHALL otherwise use applicable bound issue or pull-request
context.

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
- **AND** SHALL preserve source and location references when deduplicating a
  concern

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
