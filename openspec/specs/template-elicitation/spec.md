# template-elicitation Specification

## Purpose
Define declarative MCP input forms shared by interactive Guide template entrypoints,
including command execution, conditional follow-up input, and partial contributions.

## Requirements

### Requirement: Shared entrypoint elicitation

The system SHALL support an `elicitation` frontmatter mapping on a selected Guide skill entrypoint and on a selected Guide command template. A declaration SHALL define a named form but SHALL NOT request input by itself. A rendered `elicit` section SHALL select the named form. Guide SHALL use the same validation, capability negotiation, input-result handling, URI-keyword precedence, and template keyword context for commands and skills.

#### Scenario: Command requests declared input

- **WHEN** a command renders an `elicit` section for a declared form whose required properties are unresolved
- **THEN** Guide SHALL issue the same capability-negotiated MCP input request used for a skill entrypoint
- **AND** SHALL render the invoked section after values are available
- **AND** SHALL make accepted values available through `kwargs` inside the invoked section

#### Scenario: Uninvoked declaration does not request input

- **WHEN** a selected template declares a form but no rendered branch invokes it
- **THEN** Guide SHALL not request that form

#### Scenario: Explicit URI values satisfy an invoked form

- **WHEN** command URI keywords satisfy an invoked form's required properties
- **THEN** Guide SHALL render the command without requesting that form
- **AND** SHALL preserve those values in the normal command template keyword context

#### Scenario: Entry point has no invoked form

- **WHEN** a selected skill or command renders no `elicit` section
- **THEN** its existing rendering and request behaviour SHALL remain unchanged

### Requirement: Elicitation form declaration schema

Each named form SHALL declare a non-empty `message` and an object schema with a non-empty `properties` mapping. Properties SHALL use only `string`, `integer`, `number`, or `boolean` types. An `enum`, when provided, SHALL contain primitive values. A form's required property names SHALL be declared in that form. A later rendered `elicitation` mapping MAY replace an earlier declaration with the same form identifier.

#### Scenario: Invalid form declaration

- **WHEN** an elicitation form has an unsupported property type or duplicate identifier in one mapping
- **THEN** Guide SHALL report a frontmatter validation diagnostic

#### Scenario: Explicit URI values satisfy a command form

- **WHEN** command URI keywords satisfy an invoked form's required properties
- **THEN** Guide SHALL render the invoked section without requesting that form
- **AND** SHALL preserve those values in the normal command template keyword context

#### Scenario: Defaulted form is visible to the template

- **WHEN** an invoked form is completed with its schema defaults or render fallback
- **THEN** the template context SHALL expose that form at `elicitation.defaulted_forms.<form-name>`

#### Scenario: Numeric field constraint

- **WHEN** an elicitation integer or number field declares `minimum` or `maximum`
- **THEN** Guide SHALL reject supplied and default values outside that inclusive range
- **AND** SHALL return the ordinary input validation failure

#### Scenario: Typed URI value selects a conditional branch

- **WHEN** a URI keyword supplies a value for a declared numeric or boolean elicitation field
- **THEN** Guide SHALL validate and normalise it to the declared field type
- **AND** SHALL use the normalised value when evaluating `when` conditions

#### Scenario: Entry point has no declared form

- **WHEN** a selected skill or command has no `elicitation` frontmatter
- **THEN** its existing rendering and request behaviour SHALL remain unchanged

#### Scenario: Non-interactive document delivery

- **WHEN** ordinary document content is served through a category, collection, or general content request
- **THEN** Guide SHALL NOT evaluate `elicitation` frontmatter
- **AND** SHALL deliver the document through the existing non-interactive path

### Requirement: Consistent form delivery across MCP protocol generations

The system SHALL deliver a selected entrypoint's declared elicitation forms so that legacy MCP clients and MCP `2026-07-28` clients obtain the same effective form declarations and, once values are supplied, the same rendered output.

#### Scenario: Modern client receives applicable forms

- **WHEN** a client negotiating MCP `2026-07-28` selects an entrypoint with unresolved required form properties
- **THEN** Guide SHALL return an input request describing every currently applicable form
- **AND** SHALL render the entrypoint after the accepted values are returned

#### Scenario: Supplied URI values render on a modern client

- **WHEN** a modern client selects an entrypoint with URI keywords that satisfy every applicable form
- **THEN** Guide SHALL render the entrypoint without requesting input
- **AND** the rendered output SHALL equal that produced for a legacy client

#### Scenario: Legacy client keeps current behaviour

- **WHEN** a legacy client selects an entrypoint with a declared form
- **THEN** Guide SHALL continue to collect the applicable forms through the legacy sequential request path

### Requirement: Deterministic fallback when no form is presented

The system SHALL make the outcome deterministic when a client cannot or does not present an elicitation form. An entrypoint declaring `fallback: render` SHALL render with instructions that tell the agent exactly how to obtain the missing choice from the user.

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

The system SHALL document the form shapes verified to behave consistently across the supported agents, and SHALL identify shapes known to be unreliable.

#### Scenario: Authoring guidance records agent outcomes

- **WHEN** a form shape is adopted or rejected during this change
- **THEN** the authoring guidance SHALL record the shape and the agents on which it was verified or found unreliable

### Requirement: Dynamic choice sources for commands and skills

The system SHALL allow a string property in a command or skill elicitation form to declare a `source` that supplies its `enum` from the bound project before the form is requested. The sources SHALL be `workflow-phases`, `project-categories`, and `project-collections`. The `source` marker SHALL NOT be delivered to the client.

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

The system SHALL send each form to legacy and `2026-07-28` clients with a requested schema whose top-level keys are limited to `$schema`, `type`, `properties` and `required`, and whose property definitions carry no generated `title`, because strict clients reject other keys and cancel the request before presenting a form.

#### Scenario: Legacy form schema is accepted by a strict client

- **WHEN** a legacy client is sent a declared form
- **THEN** the requested schema SHALL contain no top-level key outside the permitted subset
- **AND** no property definition SHALL contain a `title` or any key outside the declared field subset

#### Scenario: Modern form schema matches the legacy schema

- **WHEN** a form declares extra top-level or property keys
- **THEN** a `2026-07-28` client SHALL receive the same permitted subset as a legacy client

### Requirement: Optional properties are deliverable on every protocol

The system SHALL deliver a form that has optional (non-required) properties to legacy clients as a valid primitive schema, so the same form works on legacy and `2026-07-28` connections.

#### Scenario: Optional property on a legacy client

- **WHEN** a form declares a property that is not required
- **THEN** a legacy client SHALL be sent that property as a plain primitive with no null type

#### Scenario: Skipped optional property with a default

- **WHEN** an accepted answer omits an optional property, or gives it as null, and the property declares a `default`
- **THEN** the resolved value SHALL be that default on both legacy and `2026-07-28` connections

### Requirement: Declarative conditional elicitation

The system SHALL allow an invoked form to declare `when` conditions over primitive URI or previously accepted elicitation values. A form is applicable only when its rendered `elicit` section is reached and every `when` condition matches a declared primitive value. The system SHALL resolve invoked forms in rendered section order, without a separate declaration-discovery pass.

#### Scenario: Branch to a follow-up form

- **WHEN** a rendered template reaches an `elicit` section whose form declares `when: {mode: [branch]}`
- **AND** `mode=branch` was supplied by URI keywords or an accepted form response
- **THEN** Guide SHALL request that form before rendering its enclosed section

#### Scenario: Skip an inapplicable branch

- **WHEN** a Mustache condition excludes a branch containing an `elicit` section
- **THEN** Guide SHALL not request that section's form regardless of its declaration

#### Scenario: Multiple immediately applicable forms

- **WHEN** rendering reaches multiple `elicit` sections with unresolved required forms
- **THEN** Guide SHALL resolve each form in rendered section order
- **AND** SHALL not scan later template branches to batch forms before rendering

#### Scenario: Branching form needs input from a prior form

- **WHEN** a reached form's `when` condition depends on a missing value from an earlier reached form
- **THEN** Guide SHALL request the supplying form first
- **AND** SHALL evaluate the dependent section when rendering reaches it after acceptance

#### Scenario: Client cannot elicit input

- **WHEN** a reached form has unresolved required properties and the client cannot present it
- **THEN** Guide SHALL apply its existing render fallback or return the existing clear missing-input guidance
- **AND** SHALL not render the invoked section with assumed values

### Requirement: Elicitation partial composition

The system SHALL update a request-local form declaration registry as the template and its partials render. A rendered `elicitation` mapping SHALL add its forms to that registry, and a later rendered declaration with the same form identifier SHALL replace the earlier declaration. Include declaration order and unrendered partials SHALL not affect the registry.

#### Scenario: Partial contributes a distinct form

- **WHEN** a partial renders an `elicitation` declaration for a distinct form
- **THEN** Guide SHALL add that form to the request-local registry before a later section invokes it

#### Scenario: Conditional partial does not contribute

- **WHEN** a partial does not render through the ordinary Mustache rendering path
- **THEN** its elicitation declarations SHALL not update the request-local form registry

#### Scenario: Duplicate partial form declaration

- **WHEN** a later rendered partial declares a form identifier already in the request-local registry
- **THEN** Guide SHALL replace the earlier declaration with the later declaration
- **AND** a later invocation of that identifier SHALL use the replacement

#### Scenario: Omitted replacement removes prior form state

- **WHEN** a later rendered declaration with an existing form identifier is omitted because its source is unavailable or its value is already supplied
- **THEN** Guide SHALL remove the earlier declaration and its non-URI form state
- **AND** an invocation of that identifier SHALL render without eliciting the earlier form

### Requirement: Elicitation validation and conditional semantics

The system SHALL normalise values according to their declared primitive field types before
validating defaults, accepted input, enum membership, numeric bounds, and `when` conditions.
Integer values supplied as finite numeric values SHALL use mathematical floor semantics. A
completed form that leaves a value needed by an applicable dependent condition unknown SHALL
fail with a clear validation result. Composition SHALL report all independently detectable,
source-aware declaration diagnostics.

#### Scenario: Fractional integer value

- **WHEN** an integer field receives the finite numeric value `-1.2`
- **THEN** Guide SHALL use `-2` for subsequent enum, bound, and conditional evaluation

#### Scenario: Optional supplier leaves a branch unknown

- **WHEN** a completed form omits an optional value used by a dependent form's `when` condition
- **THEN** Guide SHALL return a validation failure rather than silently skip the dependent form
