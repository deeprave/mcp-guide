## Context

This change is small in surface area but crosses two related systems:

- template helper rendering
- command-template UX for `:help` and `:handoff`

The existing `resource` helper already provides a model for configurable output
formatting based on feature flags. The new command helper should follow that
pattern closely enough to remain understandable, while handling a more complex
rendering shape: command name, positional arguments, keyword flags, and aliases.

## Goals

- Make command references in templates reusable and formatting-aware
- Keep the implementation close to the existing `resource` helper model
- Let `:help` benefit from a single authoritative command-formatting path
- Make `:handoff` explicit about read-vs-write intent and target path
- Replace hardcoded command/resource references in applicable templates with the
  shared helper family
- Make static documentation use `guide://` as the canonical command/reference form

## Non-Goals

- Do not redesign the full command parser or URI routing model
- Do not change the underlying command execution semantics
- Do not introduce a general-purpose template state machine beyond what is
  needed to support adjacent `command-*` helper sections

## Decisions

### Decision: Keep command rendering as a template helper, not a data-precomputed field

The `:help` template could theoretically precompute every command reference in
Python before rendering. That would solve the immediate help-display problem,
but it would not help other templates such as `:handoff` or future workflow
templates. The change should therefore live in the template helper layer.

For the narrower case where a template needs just the effective prompt name,
the template context can also expose `{{prompt}}` as a compatibility escape
hatch. New command references should still prefer the command helper family.

That same decision implies follow-through: once the helper family exists,
templates should stop hardcoding prompt-style command references or direct
resource-rendering choices where the shared helpers can express them.

### Decision: Model the new command helper after `resource`

The existing `resource` helper already establishes the pattern:

- a feature flag controls output format
- templates use a compact lambda-style syntax
- output adapts to agent/tool usage constraints

The new command helper should reuse that conceptual model rather than inventing
an unrelated templating convention.

### Decision: Use `guide://` as the canonical form in static docs

Static documentation cannot take advantage of template-time formatting flags,
prompt-prefix detection, or prompt-name overrides. It therefore should not try
to mirror every client-specific invocation form.

Static docs should:

- use `guide://...` as the primary command/reference form
- mention prompt-style invocation only as a note or occasional reminder
- avoid hardcoding `@guide` or `/guide` as the canonical syntax

This keeps the documentation stable even when prompt naming or client behavior
changes.

### Decision: Rename the resource-format flag and use a dedicated command-format flag

The command formatting choice is conceptually separate from content/resource
formatting. The existing `content-accessor` name is too implementation-shaped
and not obvious in user configuration.

This change should therefore:

- rename `content-accessor` to `format-resource`
- expose it through an explicit `FLAG_RESOURCE` constant
- add a new `format-command` flag exposed as `FLAG_COMMAND`
- expose the effective prompt name as `{{prompt}}`

`format-command` should support:

- `true`: force tool-oriented rendering
- `false`: force `guide://_...` URI rendering
- `None` / unset: use the URI form by default

`format-resource` should follow the same model:

- `true`: force `get_content("...")` rendering
- `false`: force `guide://...` URI rendering
- `None` / unset: use the URI form by default

### Decision: Allow helper sections to accumulate state across adjacent command lambdas

The requested syntax implies that:

- `{{#command}}name{{/command}}` defines the base command
- following `command-args`, `command-flags`, and `command-alias` sections
  contribute to the same rendered command reference

That requires short-lived render state during a single template expansion.

The implementation should keep that state tightly scoped to the current
`TemplateFunctions` instance and only for the immediately composed command
reference, rather than creating a broader general-purpose template state model.

### Decision: Keep `:handoff` as a single command with explicit mode flags

Instead of splitting `:handoff` into separate `:handoff/read` and
`:handoff/write` commands, keep one command with explicit `--read` and
`--write` flags. This stays closer to the current UX while making intent
explicit.

The command should reject:

- no path argument
- `--read` and `--write` together
- neither `--read` nor `--write`

## Trade-offs

### Command helper statefulness

The requested command helper syntax is convenient for template authors, but it
is more stateful than the existing `resource` helper. That introduces some
implementation complexity in `render/functions.py`.

This is acceptable because:

- the helper family is narrowly scoped
- the behavior is user-visible in high-value templates
- it reduces repeated hardcoded command formatting across templates

### URI-first default behavior

The original design considered agent-specific overrides, but the better default
is to make URI form the universal fallback.

That means:

- `format-resource = false` or unset should render `guide://...`
- `format-command = false` or unset should render `guide://_...`
- `true` should opt into tool-oriented formatting explicitly

This removes client-specific branching from the helper semantics and keeps the
default behavior aligned with the most broadly portable representation.

### Decision: Allow prompt name override via environment

Some clients now reserve or collide with `/guide` or equivalent prompt names.
The prompt registration path should therefore allow the prompt command name to
be overridden by environment variable.

Use `MCP_PROMPT_NAME` to override the default prompt name `guide`.

Examples:

- unset: prompt remains `guide`
- `MCP_PROMPT_NAME=g`: prompt becomes `@g` / `/g` depending on client prefix

This override affects prompt-style rendering and prompt registration, but does
not change the `guide://` URI scheme.

## Affected Areas

- Feature flag constants and validator registration
- Template lambda/function implementation
- Prompt registration / prompt naming
- Help template rendering
- Other templates that hardcode command or resource references
- Handoff command argument and instruction wording
- User-facing feature-flag documentation
- Static command-oriented documentation
