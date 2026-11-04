# Spec Delta

## ADDED Requirements

### Requirement: Consistent form delivery across MCP protocol generations

The system SHALL deliver a selected entrypoint's declared elicitation forms so that
legacy MCP clients and MCP `2026-07-28` clients obtain the same effective form
declarations and, once values are supplied, the same rendered output.

#### Scenario: Modern client receives applicable forms

- **WHEN** a client negotiating MCP `2026-07-28` selects an entrypoint with unresolved
  required form properties
- **THEN** Guide SHALL return an input request describing every currently applicable form
- **AND** SHALL render the entrypoint after the accepted values are returned

#### Scenario: Supplied URI values render on a modern client

- **WHEN** a modern client selects an entrypoint with URI keywords that satisfy every
  applicable form
- **THEN** Guide SHALL render the entrypoint without requesting input
- **AND** the rendered output SHALL equal that produced for a legacy client

#### Scenario: Legacy client keeps current behaviour

- **WHEN** a legacy client selects an entrypoint with a declared form
- **THEN** Guide SHALL continue to collect the applicable forms through the legacy
  sequential request path

### Requirement: Deterministic fallback when no form is presented

The system SHALL make the outcome deterministic when a client cannot or does not present
an elicitation form. An entrypoint declaring `fallback: render` SHALL render with
instructions that tell the agent exactly how to obtain the missing choice from the user.

#### Scenario: Declined form with render fallback

- **WHEN** a client declines an applicable form that declares `fallback: render`
- **THEN** Guide SHALL render the entrypoint without applying schema defaults
- **AND** SHALL expose the form under `elicitation.defaulted_forms.<form-name>`

#### Scenario: Declined form without render fallback

- **WHEN** a client declines an applicable form that does not declare `fallback: render`
- **THEN** Guide SHALL return the ordinary input-not-completed failure

#### Scenario: Legacy client never answers

- **WHEN** a legacy client does not answer an input request within the response timeout
- **THEN** Guide SHALL treat the form as unanswered and apply its render fallback, or fail when none is declared
- **AND** SHALL NOT apply the form's defaults, because no one chose them
- **AND** SHALL NOT wait indefinitely for the client

#### Scenario: Fallback never assumes a value

- **WHEN** the fallback path is used for an unresolved required property
- **THEN** Guide SHALL NOT substitute an undeclared value for it

### Requirement: Verified form patterns for portable delivery

The system SHALL document the form shapes verified to behave consistently across the
supported agents, and SHALL identify shapes known to be unreliable.

#### Scenario: Authoring guidance records agent outcomes

- **WHEN** a form shape is adopted or rejected during this change
- **THEN** the authoring guidance SHALL record the shape and the agents on which it was
  verified or found unreliable

### Requirement: Dynamic choice sources for commands and skills

The system SHALL allow a string property in a command or skill elicitation form to declare a
`source` that supplies its `enum` from the bound project before the form is requested. The
sources SHALL be `workflow-phases`, `project-categories`, and `project-collections`. The
`source` marker SHALL NOT be delivered to the client.

#### Scenario: Skill form uses a source

- **WHEN** a selected skill declares a form property with `source: project-categories`
- **THEN** Guide SHALL deliver that property with the project's category names as its `enum`

#### Scenario: Command form uses a source

- **WHEN** a selected command declares a form property with `source: project-collections`
- **THEN** Guide SHALL deliver that property with the project's collection names as its `enum`

#### Scenario: Value already supplied

- **WHEN** a positional argument or keyword already supplies the sourced property
- **THEN** Guide SHALL NOT request that form

#### Scenario: Source has no choices

- **WHEN** a sourced property would have no choices
- **THEN** Guide SHALL NOT request that form
- **AND** the entrypoint's own validation SHALL report the missing value

#### Scenario: Unrecognised source

- **WHEN** a form declares an unrecognised `source`
- **THEN** Guide SHALL remove the marker, log a warning, and treat the property as free text

### Requirement: Form schema restricted to the MCP form subset

The system SHALL send each form to legacy and `2026-07-28` clients with a requested schema
whose top-level keys are limited to `$schema`, `type`, `properties` and `required`, and whose
property definitions carry no generated `title`, because strict clients reject other keys and
cancel the request before presenting a form.

#### Scenario: Legacy form schema is accepted by a strict client

- **WHEN** a legacy client is sent a declared form
- **THEN** the requested schema SHALL contain no top-level key outside the permitted subset
- **AND** no property definition SHALL contain a `title` or any key outside the declared field subset

#### Scenario: Modern form schema matches the legacy schema

- **WHEN** a form declares extra top-level or property keys
- **THEN** a `2026-07-28` client SHALL receive the same permitted subset as a legacy client

### Requirement: Optional properties are deliverable on every protocol

The system SHALL deliver a form that has optional (non-required) properties to legacy clients as
a valid primitive schema, so the same form works on legacy and `2026-07-28` connections.

#### Scenario: Optional property on a legacy client

- **WHEN** a form declares a property that is not required
- **THEN** a legacy client SHALL be sent that property as a plain primitive with no null type

#### Scenario: Skipped optional property with a default

- **WHEN** an accepted answer omits an optional property, or gives it as null, and the property
  declares a `default`
- **THEN** the resolved value SHALL be that default on both legacy and `2026-07-28` connections


## MODIFIED Requirements

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
- **AND** the client does not support MCP elicitation or does not present the form
- **THEN** a form that declares `fallback: render` SHALL cause the entrypoint to render with
  instructions that list the available choices and direct the agent to ask the user to
  select one before proceeding
- **AND** a form without `fallback: render` SHALL cause Guide to return clear guidance
  naming the URI keywords currently required to progress, without rendering the entrypoint
- **AND** Guide SHALL NOT render the entrypoint with assumed values
