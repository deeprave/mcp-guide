# Spec Delta

## ADDED Requirements

### Requirement: Asynchronous template execution
The renderer SHALL execute document, partial, and renderable frontmatter
templates through one asynchronous Mustache rendering path. It SHALL await
registered asynchronous template extensions and partial resolution without
blocking other concurrent requests.

#### Scenario: Asynchronous extension in a document
- **WHEN** a document uses a registered asynchronous template extension
- **THEN** its rendered output SHALL include the awaited extension result
- **AND** the document render SHALL complete without a synchronous event-loop bridge

#### Scenario: Asynchronous extension in a partial or renderable frontmatter
- **WHEN** a partial or renderable frontmatter field uses a registered asynchronous template extension
- **THEN** it SHALL be rendered by the same asynchronous execution model
- **AND** its existing contribution and delivery semantics SHALL be retained

### Requirement: Explicit template extension registry
The renderer SHALL register Guide callable template extensions through an
explicit per-render extension registry rather than exposing callables as
ordinary template data. It SHALL support both section extensions and direct
interpolation extensions using the renderer's declared protocols.

#### Scenario: Registered section extension
- **WHEN** a template invokes a registered section extension
- **THEN** the renderer SHALL execute it according to the declared section-extension protocol
- **AND** ordinary context lookup SHALL remain available to the extension as required for its output

#### Scenario: Registered interpolation extension
- **WHEN** a template interpolates a registered direct extension
- **THEN** the renderer SHALL evaluate it according to the declared interpolation-extension protocol
- **AND** apply normal Mustache escaping semantics

#### Scenario: Callable context value is not an extension
- **WHEN** a template context contains a callable that is not registered as an extension
- **THEN** the renderer SHALL NOT execute that callable as a template extension

### Requirement: Legacy template compatibility during renderer upgrade
The renderer SHALL preserve the agent-visible output and error behaviour of
templates supported by the prior Chevron 0.14.0 integration, except where this
change explicitly adds supported Mustache behaviour.

#### Scenario: Existing template and partial render
- **WHEN** an existing Guide template uses supported variables, sections, inverted sections, partials, delimiter changes, or Guide extensions
- **THEN** it SHALL render the same agent-visible content and effective document properties as before the upgrade

#### Scenario: Existing template error
- **WHEN** an existing Guide template has invalid Mustache syntax or an extension evaluation error
- **THEN** Guide SHALL retain its structured template error result and actionable diagnostic behaviour
