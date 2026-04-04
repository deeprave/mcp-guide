## ADDED Requirements

### Requirement: Exported Frontmatter Guidance

The export instruction template SHALL explain how agents must interpret frontmatter added to exported content.

The guidance SHALL explain:
- `type` determines whether exported content is user-facing information, agent-only information, or agent-only instruction content
- `instruction` overrides default handling and must be followed when present

#### Scenario: First export explains exported frontmatter
- **WHEN** `export_content` returns instructions to write exported content to disk
- **THEN** the message explains that the exported file contains frontmatter with `type` and `instruction`
- **AND** the message tells the agent to apply those fields when the exported file is read later

#### Scenario: Export reference explains exported frontmatter
- **WHEN** `get_content` or `export_content` returns a reference to already-exported content
- **THEN** the message explains that the exported file contains frontmatter with `type` and `instruction`
- **AND** the message tells the agent how those fields affect display and execution behavior
