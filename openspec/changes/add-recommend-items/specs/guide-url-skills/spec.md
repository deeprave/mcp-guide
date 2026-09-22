## ADDED Requirements

### Requirement: Startup advertises suggested effective Guide skills
Startup delivery SHALL include a dedicated partial whose frontmatter declares
`requires-mcp-skills: true`. The partial SHALL author its Guide-skill
suggestions through the recommendation helper, producing the structured
`mcp-guide.suggested_guide_skills` value. The value SHALL be omitted when the
experiment is disabled or the partial contributes no suggestion.

#### Scenario: Experimental skills enabled at startup
- **WHEN** a project-bound session receives startup delivery while
  `mcp-skills` is enabled
- **THEN** the startup response includes structured suggested Guide skills for
  that session from the startup partial
- **AND** each suggestion identifies its authored entrypoint URI

#### Scenario: Experimental skills disabled at startup
- **WHEN** a project-bound session receives startup delivery while
  `mcp-skills` is disabled
- **THEN** the startup response omits `mcp-guide.suggested_guide_skills`
- **AND** ordinary skill catalogue access remains unchanged
