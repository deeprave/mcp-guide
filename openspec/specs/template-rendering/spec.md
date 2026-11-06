# template-rendering Specification

## Purpose
Define template rendering, partial inclusion, and document-property resolution.

## Requirements

### Requirement: Centralized Instruction Resolution
The system SHALL provide a centralized function for resolving instructions from frontmatter that supports override semantics. No content type SHALL have a fabricated default instruction; a disposition alone, once taught to the agent, conveys the required behavior without a paired prose restatement.

#### Scenario: Important instruction override
- **WHEN** frontmatter includes `instruction: ! <text>`
- **THEN** the instruction SHALL be marked as important and override regular instructions

#### Scenario: Type-based default fallback
- **WHEN** no explicit instruction is provided in frontmatter
- **THEN** the system SHALL return no default instruction, regardless of content type
- **AND** the rendered result SHALL still carry its content type as its disposition

#### Scenario: Instruction deduplication
- **WHEN** multiple sources provide the same instruction
- **THEN** the system SHALL deduplicate at sentence level

### Requirement: Template Partial Frontmatter Merging
The system SHALL merge frontmatter from the parent template and every file-backed partial that actually renders. It SHALL use centralized instruction resolution and SHALL resolve the rendered content disposition from the parent and contributing partials using established disposition precedence.

#### Scenario: Partial overrides parent instruction
- **WHEN** a partial template includes frontmatter with `instruction: ! <text>`
- **THEN** the partial's instruction SHALL override the parent template's instruction

#### Scenario: Partial provides type metadata
- **WHEN** a partial template includes `type:` frontmatter
- **THEN** the partial's type SHALL be preserved and used for instruction resolution
- **AND** the effective rendered disposition SHALL use that type when it has higher precedence than the parent disposition

#### Scenario: Conditional display behavior
- **WHEN** a template conditionally includes a partial based on data availability
- **THEN** the partial's frontmatter SHALL control whether content is displayed or treated as instructions
- **AND** only a partial that renders SHALL contribute to the effective disposition

### Requirement: Policy Include Pre-rendering

The system SHALL support a `policies:` frontmatter key declaring policy topics a
template depends on. Declared topics SHALL be pre-rendered as Mustache partials
before the main template renders.

#### Scenario: Single policy topic resolved
- **WHEN** a template declares `policies: [git/ops]` and a document is active for `git/ops`
- **THEN** that document is pre-rendered and registered as partial `git/ops` before main rendering

### Requirement: Policy include topic resolution

For each declared topic, Guide SHALL resolve the `policies` category using the
active project patterns and topic sub-path filter, then pre-render every matched
document individually.

#### Scenario: Multiple policy topics resolved
- **WHEN** a template declares `policies: [git/ops, testing]`
- **THEN** each topic is resolved and pre-rendered independently before main rendering

### Requirement: Policy include partial registration and frontmatter

Guide SHALL preserve each policy document's frontmatter and resolve its
contribution under ordinary partial-frontmatter rules, combining and
deduplicating fields rather than stripping them. It SHALL register pre-rendered
content as a Mustache partial under the topic key.

Templates SHALL reference pre-rendered policy content using standard mustache partial syntax:
`{{> topic/key}}` (e.g. `{{> git/ops}}`).

#### Scenario: Composable topic — multiple documents
- **WHEN** the project's patterns match multiple documents under a topic
- **THEN** all matched documents are concatenated as the partial content for that topic

#### Scenario: Partial referenced in template
- **WHEN** a template contains `{{> git/ops}}`
- **THEN** it renders the pre-rendered policy content for the `git/ops` topic

### Requirement: Rendered policy partial disposition contribution

The effective rendered disposition SHALL include only policy documents whose
registered partials actually render.

#### Scenario: Policy partial changes disposition
- **WHEN** a rendered policy document has a higher-precedence `type:` than its parent template
- **AND** its policy partial is referenced by the parent
- **THEN** the final rendered content SHALL carry the policy document's effective disposition

#### Scenario: Unreferenced policy partial
- **WHEN** a policy topic is pre-rendered but its partial is not referenced by the parent template
- **THEN** its frontmatter SHALL NOT affect the final rendered disposition

### Requirement: Policy Partial Context Variables

The system SHALL provide per-document context variables when pre-rendering each policy document.

Each policy document SHALL be rendered with:
- `policy_topic` — the declared topic name (e.g. `git/ops`)
- `policy_category` — the category containing the document (always `policies`)
- `policy_path` — the relative path of the matched document within the category

#### Scenario: Context variables available in policy document
- **WHEN** a policy document is pre-rendered
- **THEN** `policy_topic`, `policy_category`, and `policy_path` are available as template variables

#### Scenario: Distinct paths for distinct documents
- **WHEN** multiple documents match a composable topic
- **THEN** each document is pre-rendered with its own `policy_path` value

### Requirement: Missing Policy Placeholder

The system SHALL render a `_missing_policy` system template as the partial content when a
declared policy topic resolves to zero documents.

The `_missing_policy` template SHALL render content that includes the `INSTRUCTION_MISSING_POLICY`
constant, which informs the AI assistant that no policy has been selected for that topic and it
should proceed without enforcing any specific preference.

The placeholder is informational only — it SHALL NOT cause template rendering to fail.

#### Scenario: No documents selected — placeholder rendered
- **WHEN** a template declares a policy topic and no documents match the project's patterns
- **THEN** the `_missing_policy` template is rendered as the partial content for that topic

#### Scenario: Placeholder is informational
- **WHEN** the `_missing_policy` placeholder is rendered
- **THEN** the AI assistant is instructed to proceed without a specific policy preference
      for the topic, not to treat the absence as an error

### Requirement: Unbound-session template rendering

The system SHALL support rendering `_system/` category templates when no project is
bound to the current session.

#### Scenario: Render _system template with unbound session
- **WHEN** `render_content(pattern, "_system", extra_context)` is called
- **AND** no project is bound to the current session
- **THEN** the template renders without raising an exception
- **AND** `project.*` variables in the rendered output are empty or absent
- **AND** `feature_flags` contains global flags
- **AND** `agent.*` and `client.*` variables are present if bootstrap data is available

### Requirement: Unbound-session template context values

When no project is bound, `project.*` SHALL be empty or absent, `flags` SHALL
contain global feature flags only, and `feature_flags` SHALL contain global flags.

#### Scenario: Unbound project and flags context
- **WHEN** an _system template renders without a bound project
- **THEN** project values are absent and flags use only global feature values

### Requirement: Unbound-session agent and server context values

When no project is bound, `agent.*` SHALL use available MCP bootstrap agent
information and `client.*` SHALL use available TaskManager cached data, or both
shall be absent. `server.*`, formatting values, `tool_prefix`, `@`, and transient
timestamp values SHALL always be available.

#### Scenario: Unbound auxiliary template context
- **WHEN** an _system template renders without a bound project
- **THEN** available agent/client context and always-available server context remain usable

### Requirement: Unbound-session template missing-project safety

The rendering pipeline SHALL NOT raise an exception when called with an unbound session.
Any missing project variable SHALL silently default to its empty value, consistent with
how `_build_project_context()` already behaves.

#### Scenario: Render _system template with bound session is unchanged
- **WHEN** `render_content(pattern, "_system", extra_context)` is called
- **AND** a project is bound to the current session
- **THEN** the template renders identically to existing behaviour
- **AND** all project, flag, workflow and client_working_dir variables are populated
  as before

#### Scenario: Missing project variable does not raise
- **WHEN** a `_system/` template references `{{project.name}}` with no bound project
- **THEN** the mustache renderer produces an empty string for that variable
- **AND** no exception is raised

### Requirement: Template Context Preserves Display-Safe Flag Values

Templates SHALL be able to display configured flag values using stable,
user-facing representations without changing the generic list-wrapping
semantics used elsewhere in the rendering system.

The display-oriented flag projections used by templates SHALL build on the
canonical feature-value display behavior rather than introducing a separate
workflow-specific formatter.

#### Scenario: Custom workflow list renders as plain phase names for display
- **GIVEN** the configured workflow flag value is `[discussion, implementation, check, review]`
- **AND** the rendering system continues to use generic indexed list wrappers for list iteration
- **WHEN** a project or workflow-aware template displays the configured flag value for the user
- **THEN** the rendered output uses plain phase names
- **AND** it does NOT render the internal wrapper-object representation containing `value`, `first`, and `last`

#### Scenario: Dict-like flag renders as stable display text
- **GIVEN** a configured flag value is a dict or contains nested dict/list values
- **WHEN** a template displays that flag value through a display-oriented flag projection
- **THEN** the rendered output is a stable user-facing string representation
- **AND** it does NOT expose internal wrapper-object representations from generic list conversion

#### Scenario: Raw structured flags remain available separately from display projections
- **GIVEN** the template context exposes both raw flag dictionaries and display-oriented flag projections
- **WHEN** a template or renderer needs structured access to configured flag values
- **THEN** it can continue to read the raw flag dictionaries without losing bool/list/dict structure
- **AND** this workflow-render fix only changes the display-oriented projection used for direct user-facing output

#### Scenario: Generic list rendering semantics remain unchanged
- **GIVEN** a non-workflow list in template context
- **WHEN** template rendering prepares that list for iteration
- **THEN** the system continues to expose the generic indexed wrapper behavior used by existing templates
- **AND** this workflow-render fix does not change global list conversion behavior

### Requirement: Bounded template and partial content

The system SHALL check a template or partial source byte size against the global
`max-content-limit` before parsing or rendering it. It SHALL check each rendered
template before document formatting.

Policy-partial discovery and rendering SHALL receive the active global limits.
The server SHALL bound aggregate rendered policy content before joining it for
the parent template.

#### Scenario: Oversized template source is rejected
- **WHEN** a selected template exceeds `max-content-limit`
- **THEN** it fails with `max_size_exceeded` before parsing or rendering

#### Scenario: Oversized rendered template is rejected
- **WHEN** rendering produces content exceeding `max-content-limit`
- **THEN** no oversized result is passed to document formatting

### Requirement: Canonically contained frontmatter partials

The system SHALL resolve each relative frontmatter partial reference from the
directory of its including template and SHALL load it only when the final
canonical file target, after independent partial-filename and extension
resolution, is contained within the configured document root.

#### Scenario: Parent-relative partial remains inside the document root
- **WHEN** a nested template references a partial with `..` path components
- **AND** the final canonical partial target remains within the document root
- **THEN** the system SHALL render that partial using the existing partial
  composition behaviour

### Requirement: Absolute frontmatter partial containment

An absolute frontmatter partial reference SHALL be accepted only when its final
canonical target is inside the configured document root.

#### Scenario: Absolute partial reference remains inside the document root
- **WHEN** frontmatter names a partial with an absolute path whose final
  canonical target is inside the configured document root
- **THEN** the system SHALL load that partial

### Requirement: Unsafe frontmatter partial isolation

Frontmatter partial resolution SHALL use server-side document-root containment,
not client-filesystem resolution semantics. It SHALL not read, render, or merge
frontmatter from an unsafe target.

#### Scenario: Home-anchored or environment-variable partial reference
- **WHEN** frontmatter names a partial using home-anchored or
  environment-variable expansion syntax
- **THEN** the system SHALL reject that partial reference without expansion
- **AND** it SHALL not read content from the named host path

#### Scenario: Relative partial escapes the document root
- **WHEN** a relative frontmatter partial reference canonically resolves outside
  the configured document root
- **THEN** the system SHALL reject that partial reference
- **AND** it SHALL not render the outside file's content

#### Scenario: In-root symlink points outside the document root
- **WHEN** a frontmatter partial reference resolves through a symlink whose
  canonical target is outside the configured document root
- **THEN** the system SHALL reject that partial reference
- **AND** it SHALL not read the symlink target

#### Scenario: One unsafe partial does not suppress safe rendering
- **WHEN** a template declares both a safe in-root partial and an unsafe
  partial reference
- **THEN** the system SHALL render the template and the safe partial
- **AND** it SHALL omit the unsafe partial without exposing its content
- **AND** it SHALL log a non-sensitive warning

### Requirement: Elicitation-aware partial property collection

Before rendering an interactive skill or command entrypoint, the template system
SHALL collect only eligible parent and partial input declarations needed to resolve
elicitation. It SHALL discard unrelated headers after resolving the state it needs
and SHALL NOT merge preflight delivery properties into rendered output. It SHALL
include frontmatter-only partials declared through the existing parent partial
list, while retaining existing output interpolation rules.

#### Scenario: Collect properties before interactive rendering

- **WHEN** an interactive command or skill has parent or eligible partial
  elicitation frontmatter
- **THEN** the renderer SHALL make the composed declarations available before
  rendering output
- **AND** SHALL render output only after the interaction has resolved the
  applicable required values

#### Scenario: Do not interpolate a property-only partial

- **WHEN** a listed partial contributes frontmatter properties but is not
  referenced by a Mustache partial tag
- **THEN** the renderer SHALL not append or otherwise interpolate that partial's
  body content
- **AND** SHALL retain only its eligible elicitation contribution for input resolution

#### Scenario: Status skips setup partials

- **GIVEN** status declares `user/information`, agent information is available and workflow has a known phase
- **WHEN** status is delivered after preflight
- **THEN** skipped setup partials SHALL NOT contribute delivery metadata
- **AND** status SHALL retain `user/information`

#### Scenario: Rendered contributors remain authoritative

- **GIVEN** a parent and partial declare different disposition, instruction or cache settings
- **WHEN** the partial actually renders after input resolution
- **THEN** final metadata SHALL follow existing rendering composition rules
- **AND** preflight inspection SHALL NOT add another metadata contributor

### Requirement: Universal frontmatter template evaluation

The renderer SHALL treat only `instruction`, `description`, and `elicitation`
frontmatter values as Mustache templates. It SHALL use this same fixed whitelist
for rendered documents, commands, skills and partials.

#### Scenario: Renderable frontmatter whitelist
- **WHEN** a document, command, skill, or partial renders frontmatter
- **THEN** only instruction, description, and elicitation values are evaluated as Mustache templates

### Requirement: Interactive frontmatter preflight evaluation

Interactive preflight SHALL evaluate only elicitation-related values needed for
input resolution with temporary supporting context; it SHALL NOT evaluate
unrelated renderable headers as delivery fields.

#### Scenario: Interactive preflight uses the universal whitelist

- **WHEN** interactive preflight resolves parent or partial frontmatter
- **THEN** it SHALL evaluate only elicitation-related values needed for input resolution
- **AND** it SHALL use `requires-*` and `includes` for eligibility and discovery as needed
- **AND** it SHALL discard unrelated headers before returning preflight state
- **AND** original frontmatter SHALL remain available for independent rendering with resolved inputs

### Requirement: Literal structural frontmatter and diagnostics

Structural metadata, including `includes`, `cache`, and `type`, SHALL remain
literal. Client-visible source labels in frontmatter diagnostics SHALL be
relative to the document root.

#### Scenario: Structural frontmatter remains literal

- **WHEN** a document, command, skill, or partial has structural frontmatter
  containing template syntax
- **THEN** Guide SHALL retain that value literally

#### Scenario: Source-aware diagnostic

- **WHEN** elicitation composition reports a source path to an MCP client
- **THEN** that path SHALL be relative to the document root

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

- **WHEN** a renderable frontmatter field signals `_error`, uses `recommend`, or raises an extension error
- **THEN** Guide SHALL retain successfully rendered sibling fields
- **AND** the final document result SHALL surface a clear diagnostic rather than silently discarding the error or returning unrendered metadata

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
- **THEN** the inventory runner SHALL render the shipped template inventory and its curated representative cases
- **AND** it SHALL fail when a discovered template cannot be rendered or a declared representative outcome changes

### Requirement: Explicit Chevron 0.20 extensions

Guide SHALL enable `Extension.CONDITIONAL_SECTIONS` and
`Extension.ENHANCED_ITERATORS` explicitly for Guide rendering. It SHALL NOT
enable `Extension.ALL`.

#### Scenario: Conditional iterable guard

- **WHEN** a Guide-owned template must render a heading only when an iterable has values and subsequently render that iterable
- **THEN** it SHALL use a conditional section without consuming or changing the iterable's active context before its ordinary section renders

#### Scenario: Repeated Guide-owned template sequence

- **WHEN** a Guide-owned template needs first or last item formatting
- **THEN** it SHALL use the enhanced iterator's `.first` or `.last` metadata
- **AND** it SHALL use `.` for the current scalar item rather than a Guide-injected wrapper value
