## ADDED Requirements

### Requirement: Structured recommendation metadata
The system SHALL preserve a rendered recommendation list through every public
tool, prompt, and resource response adapter. It SHALL expose a non-empty,
structured list
at `_meta["mcp-guide"]["recommendations"]` independently of the queued
additional-agent-instruction contract, and SHALL omit the key when no
recommendation exists.

#### Scenario: Recommendation and instruction coexist
- **WHEN** an outgoing response has both a queued additional agent instruction
  and rendered recommendation items
- **THEN** the response includes both Guide metadata values
- **AND** neither value replaces or serialises the other as prose

#### Scenario: Legacy response carries a recommendation
- **WHEN** a retained-client response contains rendered recommendation items
- **THEN** the response exposes the structured recommendation list through its
  Guide response metadata contract
- **AND** it preserves the existing legacy instruction field behaviour

#### Scenario: Guide skill has an invocation name and resource fallback
- **WHEN** a template recommends `Guide skill "git-commit"`
- **THEN** the delivered item identifies `git-commit` as the skill name for
  client-side selection
- **AND** it is represented as
  `{ "type": "guide-skill", "name": "git-commit", "resource_uri": "guide://$git-commit" }`
