# Spec Delta

## MODIFIED Requirements

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
- **WHEN** an agent requests `guide://$workflow-status` through Guide's `read_resource` tool or a native MCP resource read
- **THEN** the system SHALL resolve the entrypoint below `{docroot}/_skills/workflow-status/SKILL.md`
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
