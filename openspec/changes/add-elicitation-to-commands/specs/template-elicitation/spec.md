## Purpose

Define declarative MCP input forms shared by interactive Guide template entrypoints,
including command execution, conditional follow-up input, and partial contributions.

## ADDED Requirements

### Requirement: Shared entrypoint elicitation

The system SHALL support an `elicitation` frontmatter mapping on a selected Guide
skill entrypoint and on a selected Guide command template. It SHALL use the same
validation, capability negotiation, input-result handling, URI-keyword precedence,
and template keyword context for both entrypoint kinds. It SHALL NOT infer a form
from an entrypoint name.

Each named form SHALL declare a non-empty `message` and an object schema with a
non-empty `properties` mapping. Properties SHALL use only `string`, `integer`,
`number`, or `boolean` types. An `enum`, when provided, SHALL contain primitive
values. A form's required property names SHALL be declared in that form. Form
identifiers and property names SHALL be unique across the effective entrypoint
declaration.

#### Scenario: Command requests declared input

- **WHEN** a selected command has an effective elicitation form with missing
  required properties
- **THEN** Guide SHALL issue the same capability-negotiated MCP input request used
  for a skill entrypoint
- **AND** SHALL render the command only after the required values are available
- **AND** SHALL make accepted values available through `kwargs` and `raw_kwargs`

#### Scenario: Explicit URI values satisfy a command form

- **WHEN** command URI keywords satisfy an effective form's required properties
- **THEN** Guide SHALL render the command without requesting that form
- **AND** SHALL preserve those values in the normal command template keyword
  context

#### Scenario: Entry point has no declared form

- **WHEN** a selected skill or command has no effective `elicitation` frontmatter
- **THEN** its existing rendering and request behaviour SHALL remain unchanged

#### Scenario: Non-interactive document delivery

- **WHEN** ordinary document content is served through a category, collection, or
  general content request
- **THEN** Guide SHALL NOT evaluate `elicitation` frontmatter
- **AND** SHALL deliver the document through the existing non-interactive path

### Requirement: Declarative conditional elicitation

The system SHALL allow a form to declare `when` conditions over primitive URI or
previously accepted elicitation values. A `when` mapping SHALL require every named
property to match one of its declared primitive values before the form is applicable.
The system SHALL evaluate applicability after each accepted input result and SHALL
request only applicable forms whose required properties remain unresolved.

#### Scenario: Branch to a follow-up form

- **WHEN** a command or skill receives `mode=branch` from URI keywords or an
  accepted form response
- **AND** a second form declares `when: {mode: [branch]}` and requires `reference`
- **THEN** Guide SHALL request `reference` before rendering

#### Scenario: Skip an inapplicable branch

- **WHEN** a command or skill receives `mode=main`
- **AND** a second form declares `when: {mode: [branch, pull-request]}`
- **THEN** Guide SHALL NOT request the second form
- **AND** SHALL render after every applicable form is satisfied

#### Scenario: Multiple immediately applicable forms

- **WHEN** more than one form is applicable from the URI keyword context and has
  missing required properties
- **THEN** a modern MCP response SHALL request all of those forms together
- **AND** a legacy interaction SHALL collect the same forms through its existing
  compatible elicitation path

#### Scenario: Branching form needs input from a prior form

- **WHEN** a form's `when` condition cannot yet be evaluated because it depends on
  a missing property from another form
- **THEN** Guide SHALL first request the form that supplies that property
- **AND** after acceptance SHALL issue a follow-up input request if the condition
  becomes true
- **AND** SHALL retain previously accepted values for the original request while
  processing the follow-up

#### Scenario: Client cannot elicit input

- **WHEN** an applicable form has unresolved required properties
- **AND** the client does not support MCP elicitation
- **THEN** Guide SHALL return clear guidance naming the URI keywords currently
  required to progress
- **AND** SHALL NOT render the entrypoint with assumed values

### Requirement: Elicitation partial composition

The system SHALL treat `elicitation` as a composable document property. The selected
parent and each contributing partial SHALL combine distinct form declarations into
one effective entrypoint declaration before input is requested. A partial excluded by
its existing frontmatter requirements SHALL not contribute a form. Duplicate form
identifiers or property names across contributing documents SHALL fail with a clear
frontmatter diagnostic rather than silently selecting one declaration.

#### Scenario: Partial contributes a distinct form

- **WHEN** a command or skill parent includes a partial with a distinct
  `elicitation` form
- **THEN** the partial's form SHALL be considered together with the parent's forms
- **AND** accepted values SHALL be available to both parent and partial template
  contexts

#### Scenario: Conditional partial does not contribute

- **WHEN** a partial with an elicitation declaration is excluded by its
  `requires-*` frontmatter
- **THEN** Guide SHALL NOT request that partial's form

#### Scenario: Duplicate partial form declaration

- **WHEN** the parent and a contributing partial declare the same form identifier
  or property name
- **THEN** Guide SHALL fail the selected entrypoint with a clear diagnostic
- **AND** SHALL NOT issue an ambiguous input request

### Requirement: Frontmatter-only elicitation partials

The system SHALL allow a frontmatter partial to contribute document properties,
including `elicitation`, without emitting body content. A partial named in the
parent's frontmatter partial list SHALL be processed for effective properties even
when it is not interpolated through a Mustache partial tag. Its body SHALL NOT be
included in rendered output unless the parent also interpolates it through the
existing partial mechanism.

#### Scenario: Property-only partial supplies a form

- **WHEN** a command or skill lists a partial containing only frontmatter that
  declares an elicitation form
- **THEN** Guide SHALL process and combine that form
- **AND** SHALL not add body content from that partial to the rendered entrypoint

#### Scenario: Property-only partial has no form

- **WHEN** a parent lists a frontmatter-only partial that contributes no
  elicitation declaration
- **THEN** Guide SHALL preserve the existing composed-property behaviour
- **AND** SHALL not change the rendered body solely because the partial was listed
