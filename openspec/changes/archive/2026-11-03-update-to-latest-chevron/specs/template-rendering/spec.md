# Spec Delta

## ADDED Requirements

### Requirement: Synchronous renderer compatibility gate
Before enabling asynchronous rendering, Guide SHALL validate the selected
`chevron-ng` release as a synchronous drop-in replacement for the previous
Chevron integration. The compatibility gate SHALL retain Guide's existing
partial security, contribution tracking, frontmatter, limits, and structured
error behaviour.

#### Scenario: Existing synchronous template and partial render
- **WHEN** Guide renders an existing template using the selected synchronous renderer
- **THEN** it SHALL retain the agent-visible content and effective document properties produced by the prior renderer
- **AND** it SHALL retain the established partial containment and contribution behaviour

#### Scenario: Synchronous compatibility failure
- **WHEN** the selected synchronous renderer changes supported legacy behaviour
- **THEN** Guide SHALL not proceed to asynchronous rendering migration
- **AND** the dependency upgrade SHALL be corrected or reverted before continuing

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

### Requirement: Renderable frontmatter extension profile and diagnostics
The renderer SHALL apply an explicit frontmatter extension profile to
renderable frontmatter fields. The profile SHALL retain contextual interpolation
extensions required by those fields, including `prompt` and `tool_prefix`, and
SHALL preserve `_error` and field-rendering diagnostics through the final
rendered document result.

`recommend` SHALL produce a clear frontmatter authoring diagnostic because
recommendations require an active delivery session and rendered-content
footnotes.

#### Scenario: Contextual extension in renderable frontmatter
- **WHEN** an instruction or description uses `prompt` or `tool_prefix`
- **THEN** the field SHALL render the extension result
- **AND** it SHALL not require the value to be injected as ordinary context data

#### Scenario: Frontmatter extension error
- **WHEN** a renderable frontmatter field signals `_error`, uses `recommend`,
  or raises an extension error
- **THEN** Guide SHALL retain successfully rendered sibling fields
- **AND** the final document result SHALL surface a clear diagnostic rather
  than silently discarding the error or returning unrendered metadata

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

### Requirement: Production template inventory compatibility checks
Guide SHALL provide a standalone production-template inventory runner outside
the pytest framework. The runner SHALL discover all shipped renderable
templates, render curated representative template and partial compositions
through Guide's public rendering boundary, and assert each declared expected
result or output fragment.

#### Scenario: Renderer upgrade inventory run
- **WHEN** a renderer dependency or enabled renderer extension changes
- **THEN** the inventory runner SHALL render the shipped template inventory and
  its curated representative cases
- **AND** it SHALL fail when a discovered template cannot be rendered or a
  declared representative outcome changes

### Requirement: Explicit Chevron 0.20 extensions
Guide SHALL enable `Extension.CONDITIONAL_SECTIONS` and
`Extension.ENHANCED_ITERATORS` explicitly for Guide rendering. It SHALL NOT
enable `Extension.ALL`.

#### Scenario: Conditional iterable guard
- **WHEN** a Guide-owned template must render a heading only when an iterable
  has values and subsequently render that iterable
- **THEN** it SHALL use a conditional section without consuming or changing the
  iterable's active context before its ordinary section renders

#### Scenario: Repeated Guide-owned template sequence
- **WHEN** a Guide-owned template needs first or last item formatting
- **THEN** it SHALL use the enhanced iterator's `.first` or `.last` metadata
- **AND** it SHALL use `.` for the current scalar item rather than a
  Guide-injected wrapper value
