# Spec Delta

## MODIFIED Requirements

### Requirement: Templates render recommendation items into their document
The system SHALL provide a `recommend` template helper. Each invocation SHALL
render its enclosed value, classify an explicit `skill:`, `command:`,
`content:`, or `tool:` prefix, and render fluent Guide wording followed by a
literal Markdown footnote. An unprefixed value SHALL be treated as `content:`.
The footnote SHALL contain compact fenced JSON with the type, name, and usable
URI or configured tool invocation. The helper SHALL NOT infer an item from
ordinary response prose.

#### Scenario: Template recommends a skill
- **WHEN** a template directs an agent to the `guide-git-commit` Guide skill and
  renders `{{#recommend}}skill:guide-git-commit{{/recommend}}`
- **THEN** its ordinary rendered content contains `Guide skill "guide-git-commit"`
- **AND** its rendered footnote contains `guide://$guide-git-commit` and the
  configured `use_skill("guide-git-commit")` invocation
