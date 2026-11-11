# Elicitation Authoring Guide

Elicitation lets an interactive Guide entrypoint ask a connected MCP client for the values it
needs at the point its template section renders. It is shared by command and skill entrypoints:
declare a form in frontmatter, invoke it from the body, and the same resolver handles URI values,
modern multi-round input, and legacy sequential input.

Use this guide with [Command Authoring](authoring-command.md) or
[Skills Authoring](authoring-skills.md). It describes only the shared input contract.

## Where elicitation applies

Declare `elicitation` only on an interactive command or the selected `SKILL.md` entrypoint.
Guide resolves a form only when its `elicit.<form-name>` section renders. A command supports native command resources,
`guide://_command` resource reads, and underscore, colon, and semicolon prompt routes. A skill
supports its selected `guide://$skill-name` entrypoint.

Ordinary documents and non-entrypoint skill members do not elicit. An entrypoint may compose a form
from a partial listed in `includes`, but the partial declaration becomes available only when normal
Mustache rendering reaches `{{> partial}}`. `requires-*` is evaluated before that partial is loaded.

Invalid frontmatter is an authoring error. A later rendered declaration with the same form identifier
replaces the earlier declaration for the rest of that request; include-list order and unrendered
partials have no effect.

## Form declaration

`elicitation` is a mapping from a local form identifier to a form declaration. Every form needs a
non-empty `message` and an object JSON Schema with a non-empty `properties` mapping.

```yaml
elicitation:
  review-target:
    message: Choose what to review.
    schema:
      type: object
      properties:
        mode:
          type: string
          enum: [uncommitted, branch, pull-request]
          description: Review target type.
      required: [mode]
```

Declare a form in frontmatter, then invoke it explicitly around the instructions that need its values:

```mustache
{{#elicit.review-target}}
Reviewing `{{kwargs.mode}}`.
{{/elicit.review-target}}
```

The lambda renders only its enclosed section after the form resolves. A false Mustache branch never
invokes its form. Reusing a form section in the same request reuses its accepted values.

Supported property types are `string`, `integer`, `number`, and `boolean`. `enum` values and
defaults must use the declared primitive type. `required` must name properties in that same form.
Guide sends clients only the MCP form-schema subset: `type`, `properties` and `required` (and
`$schema`) at the top level, and `type`, `enum`, `description`, `default`, `minimum`, `maximum` and
`pattern` on each property. Other keys, including `title`, are dropped on both protocol generations
because strict clients reject them; Guide logs one warning per form naming any dropped keys (for
example `maxLength` or `format`), so a constraint that is not enforced is visible to the author. Use
`description` to help the user understand a field.
Dynamic properties, described below, are filled by Guide for commands and skills.

### Dynamic choice sources

Commands and skills may mark a string property with `source` to derive its `enum` from the bound
project before the form is delivered. Guide removes the marker, so the client receives an ordinary
`enum`.

| Source | Choices |
| --- | --- |
| `workflow-phases` | The enabled workflow phases, omitting the active phase. |
| `project-categories` | The names of the project's categories. |
| `project-collections` | The names of the project's collections. |

```yaml
elicitation:
  choose-category:
    message: Choose a category from this project.
    fallback: render
    schema:
      type: object
      properties:
        name: {type: string, source: project-categories}
      required: [name]
```

A form is omitted, rather than requested, when a positional argument or keyword already supplies its
value, or when its source has no choices (for example a project without collections). Its section
renders without form values, so the command or skill then applies its own validation and reports a
missing name as it would be without a form.
An unrecognised `source` is logged and its marker removed; a static `enum` declared on the same
property is still sent to the client, so omit it if the property should be free text.

Shipped commands share the `_partials/_choose-category` and `_partials/_choose-collection` partials.
Those partials invoke their own forms when rendered. A command lists the partial in `includes`,
renders it with `{{> choose-category}}` or `{{> choose-collection}}`, and reads the answer from
`kwargs.name` when no positional argument was supplied:

```mustache
{{#args.0.value}}Use the {{tool_prefix}}category_collection_remove tool with type: 'category' and name: '{{args.0.value}}'{{/args.0.value}}
{{^args.0.value}}{{#kwargs.name}}Use the {{tool_prefix}}category_collection_remove tool with type: 'category' and name: '{{kwargs.name}}'{{/kwargs.name}}{{/args.0.value}}
```

Sources read the template context built for the current request and are resolved on every
request, including each continuation on the modern protocol. They therefore reflect the
configuration at that moment; a name that no longer exists is rejected by the command's own
validation.

An `enum` is the portable way to express a simple choice. A client may display it as a select,
radio group, or another suitable control; the precise visual presentation is client-specific and is
not a Guide contract. A free-text string remains a text field.

### Typed fields and defaults

```yaml
elicitation:
  options:
    message: Configure the run.
    schema:
      type: object
      properties:
        attempts:
          type: integer
          minimum: 1
          default: 3
        threshold:
          type: number
          default: 0.8
        dry_run:
          type: boolean
          default: false
        label:
          type: string
      required: [label]
```

Guide normalises supplied primitive values to the declared type and validates enums, numeric
`minimum`/`maximum` constraints, string `pattern` constraints, and defaults. A `pattern` is a
regular expression applied to the complete string value (Guide uses a full match); it is useful
for constraining free-text identifiers such as branch names. Patterns must be valid, non-empty
regular expressions and may only be declared on string properties.
For URI input, text is normalised only against the declared field: a string field can therefore
receive the literal text `true` or `false`, while a boolean field receives a boolean value.

URI keywords take precedence over elicited answers. `false` and `0` are values, not missing input;
only an omitted, null, or blank string required field is unresolved.

```text
guide://_review?mode=uncommitted
guide://$workflow-review?mode=branch&reference=feature/example
```

## Help and non-interactive clients

Guide resolves command help before elicitation. Asking for help must describe the command without
opening an input request.

If elicitation is unavailable, every required field in a form may use a schema `default`. Guide
uses those defaults and exposes the state to Mustache under
`elicitation.defaulted_forms.<form-name>`. The form name `defaulted` remains valid because the
internal marker is `defaulted_forms`, not `defaulted`.

```mustache
{{#elicitation.defaulted_forms.review-target}}
No target was supplied; using the documented default.
{{/elicitation.defaulted_forms.review-target}}
```

Alternatively, `fallback: render` lets the entrypoint render without unresolved values when it can
obtain the missing information in its own instructions. A cancelled form uses its defaults when
they are complete, otherwise the render fallback. A declined form with `fallback: render` also
renders, but never applies defaults; some clients (for example Claude Code on MCP 2026-07-28)
decline an input request automatically without showing a form, so the entrypoint must carry its
own instructions for asking the user. A declined form without `fallback: render` remains a
failure. On the legacy path, a request the client leaves unanswered for the response timeout
(currently 120 seconds, from `elicitation_timeout_seconds()`) is treated like a decline: it renders
the `fallback: render` path, or fails without one, and never applies defaults, because nobody chose
them. Without a complete default or `fallback: render`, Guide returns a validation failure
naming the URI keywords the caller must supply.

## Branches and matching

Use `when` to create a conditional follow-up form. There is no separate `match` frontmatter key:
the `when` mapping is the match expression. Each key names an effective form property and each
value is one permitted primitive or a list of permitted primitives.

```yaml
elicitation:
  target:
    message: Choose a target.
    schema:
      type: object
      properties:
        mode: {type: string, enum: [uncommitted, branch, pull-request]}
      required: [mode]
  reference:
    message: Enter the selected branch or pull request.
    when:
      mode: [branch, pull-request]
    schema:
      type: object
      properties:
        reference: {type: string}
      required: [reference]
```

`when` matches only when **every** condition matches. Values are compared after the supplying
field has been normalised to its declared primitive type. A condition that does not match makes the
form inapplicable. A condition whose value is not yet known is an authoring error at that section:
invoke the supplying form in an earlier rendered section. Guide re-evaluates the current section
after each accepted answer, default, and cancellation. This supports multi-step flows without asking
for a branch that does not render.

For an AND match, add more keys:

```yaml
when:
  mode: pull-request
  scope: remote
```

Both `mode` and `scope` must match for the form to apply.

## Protocol behaviour and continuation state

The declaration and rendered template context are the same for all clients. The input transport is
different:

| Connection | Behaviour |
| --- | --- |
| Legacy MCP | Guide uses the legacy sequential elicitation request path for the rendered form. |
| MCP 2026-07-28 | Guide returns an `input_required` result for the rendered form. The client sends its answer on a later request. |

For the modern protocol, continuation state retains accepted values, completed forms, requested
forms, the originating entrypoint, the original URI keywords, and command positional arguments.
FastMCP seals this state before it reaches the client and unseals it before Guide receives the next
request. A changed or cross-entrypoint state is rejected before its values are used.

This is a framework integrity boundary, not an author-facing encryption feature: authors should
not place secrets in forms merely because continuation state is sealed. Treat all accepted values as
ordinary user input and use only the declared, validated primitive fields.

### Client behaviour to expect

Observed results below come from manual runs against each client during the `fix-elicitation-forms` change.
Entries marked *not yet verified* have not been observed; do not rely on them.

| Client | Protocol | Observed behaviour |
| --- | --- | --- |
| Cursor | legacy (2025-11-25) | Shows the form and returns the answer; the command then runs. One earlier run never answered and the cause is unexplained. |
| Codex | legacy (2025-06-18) | Shows the form once MCP elicitations are enabled in its approval policy (`mcp_elicitations = true`) and Guide sends only the form-schema subset. Before the schema fix it cancelled instantly. Codex CLI is *not yet verified*. |
| Claude Code | 2026-07-28 | Declines agent-initiated tool and resource calls without showing a form. A user-initiated prompt shows the form, and the answer completes the command. |
| Claude Desktop | 2026-07-28 | Declines agent-initiated calls without showing a form (the user sees the fallback list). The prompt route is *not yet verified*: the composer rejects `_` and `:` command text and a prompt needs a bound `session_id`. |
| Antigravity (IDE and CLI) | 2026-07-28 | Both share one client (`antigravity-client v1.0.0`) and cancel `input_required` immediately without showing a form. The agent builds the choice list from the fallback guidance. |

General rules that follow from these results:

- Guide sends only `type`, `properties` and `required` at the top level of a form schema, and no
  generated `title` on properties. Strict clients such as Codex reject any other key and cancel the
  request without showing a form.
- A declined, cancelled or unanswered form falls through to `fallback: render`, so the entrypoint must
  carry its own instructions for asking the user.

## Rendering accepted values

Accepted and normalised values are merged with command or skill keyword context. Use the ordinary
Mustache keyword paths for the entrypoint type, for example:

```mustache
Reviewing {{kwargs.mode}} {{kwargs.reference}}
```

The resolver never infers a form from an entrypoint name. It uses only a declared form invoked by an
`elicit.<form-name>` section in the selected interactive entrypoint or a rendered eligible partial.
