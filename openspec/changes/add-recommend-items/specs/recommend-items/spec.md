## Purpose

Provide templates with an explicit, type-agnostic way to recommend a related
Guide item without relying on an agent to extract it from prose.

## ADDED Requirements

### Requirement: Templates render recommendation items into their document
The system SHALL provide a `recommend` template helper. Each invocation SHALL
render its enclosed value, classify an explicit `skill:`, `command:`,
`content:`, or `tool:` prefix, and render fluent Guide wording followed by a
literal Markdown footnote. An unprefixed value SHALL be treated as `content:`.
The footnote SHALL contain compact fenced JSON with the type, name, and usable
URI or configured tool invocation. The helper SHALL NOT infer an item from
ordinary response prose.

#### Scenario: Template recommends a skill
- **WHEN** a template directs an agent to the `git-commit` Guide skill and
  renders `{{#recommend}}skill:git-commit{{/recommend}}`
- **THEN** its ordinary rendered content contains `Guide skill "git-commit"`
- **AND** its rendered footnote contains `guide://$git-commit` and the
  configured `use_skill("git-commit")` invocation

### Requirement: Guide-skill recommendations remain client-driven
When a template refers to a Guide skill, it SHALL pass `skill:<name>` to the
recommendation helper. The rendered footnote SHALL include
`guide://$<name>` as a resource fallback.
The server SHALL NOT retrieve, render, or execute the referenced skill as part
of rendering the referring template. A template MAY provide a visible
footnote-style reference to the fallback URI so that its instructions remain
fluent.

#### Scenario: Fluent reference accompanies a Guide-skill recommendation
- **WHEN** a template visibly directs an agent to a Guide skill and records
  `<name>` through `recommend`
- **THEN** a client can select that named skill as the next action
- **AND** a client without a skill-selection mechanism can retrieve the
  item's resource fallback
- **AND** the referring template does not embed the selected skill's response

#### Scenario: Unmarked prose mentions a skill-like name
- **WHEN** ordinary rendered prose contains a skill-like name without the
  explicit recommendation form
- **THEN** the renderer does not infer or add a footnote

#### Scenario: Template recommends a rendered expression
- **WHEN** a template renders a `recommend` helper containing context variables
- **THEN** the rendered document contains the corresponding footnote
- **AND** the helper does not require the value to match a known item type
