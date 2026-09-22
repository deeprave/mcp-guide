## Purpose

Provide templates with a structured, type-agnostic way to recommend their next
Guide item without relying on an agent to extract the recommendation from prose.

## ADDED Requirements

### Requirement: Templates can record recommendation items
The system SHALL provide a `recommend` template helper. Each invocation SHALL
render its enclosed value, append the resulting non-empty item to the current
render's ordered recommendation list, and contribute no visible marker text to
the rendered content. The enclosed value SHALL use an explicit recommendation
form; the helper SHALL NOT infer an item type from ordinary response prose.

#### Scenario: Template recommends a skill
- **WHEN** a template directs an agent to the `git-commit` Guide skill and
  renders `{{#recommend}}Guide skill "git-commit"{{/recommend}}`
- **THEN** its ordinary rendered content contains no `recommend` marker
- **AND** its recommendation list contains a Guide-skill item named
  `git-commit` with `guide://$git-commit` as its resource fallback

### Requirement: Guide-skill recommendations remain client-driven
When a template refers to a Guide skill, it SHALL use the explicit `Guide skill
"<name>"` recommendation form. The structured item SHALL make `<name>` the
primary skill identifier and include `guide://$<name>` as a resource fallback.
It SHALL expose these as `type: "guide-skill"`, `name: "<name>"`, and
`resource_uri: "guide://$<name>"`, respectively.
The server SHALL NOT retrieve, render, or execute the referenced skill as part
of rendering the referring template. A template MAY provide a visible
footnote-style reference to the fallback URI so that its instructions remain
fluent.

#### Scenario: Fluent reference accompanies a Guide-skill recommendation
- **WHEN** a template visibly directs an agent to a Guide skill and records
  `Guide skill "<name>"` through `recommend`
- **THEN** a client can select that named skill as the next action
- **AND** a client without a skill-selection mechanism can retrieve the
  item's resource fallback
- **AND** the referring template does not embed the selected skill's response

#### Scenario: Unmarked prose mentions a skill-like name
- **WHEN** ordinary rendered prose contains a skill-like name without the
  explicit Guide-skill recommendation form
- **THEN** the renderer does not infer or add a recommendation item

#### Scenario: Template recommends a rendered expression
- **WHEN** a template renders a `recommend` helper containing context variables
- **THEN** the recommendation list contains the rendered value
- **AND** the helper does not require the value to match a known item type

### Requirement: Rendered recommendations are delivered as structured metadata
The system SHALL deliver a non-empty render recommendation list through the
Guide metadata namespace as `mcp-guide.recommendations`. It SHALL preserve the
order and repeated entries authored by the template. Responses without a
recommendation SHALL omit that key.

#### Scenario: Recommendation accompanies rendered content
- **WHEN** a rendered result contains one or more recommendation items
- **THEN** the corresponding public response includes
  `mcp-guide.recommendations` as a structured list
- **AND** the rendered textual content remains otherwise unchanged

#### Scenario: No recommendation is authored
- **WHEN** a rendered result contains no recommendation item
- **THEN** the corresponding public response omits
  `mcp-guide.recommendations`
