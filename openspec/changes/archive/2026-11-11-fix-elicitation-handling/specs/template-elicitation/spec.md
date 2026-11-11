# Spec Delta

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Frontmatter-only elicitation partials

**Reason**: A declared include must not request input when its body is not selected by rendering.

**Migration**: Interpolate the partial in the relevant template branch and invoke its form with an `elicit` section.
