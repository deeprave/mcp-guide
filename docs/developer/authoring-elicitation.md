# Elicitation Authoring Guide

Elicitation lets an interactive Guide entrypoint ask a connected MCP client for the values it
needs before Guide renders the entrypoint. It is shared by command and skill entrypoints: define a
form once in frontmatter and the same resolver handles URI values, modern multi-round input, and
legacy sequential input.

Use this guide with [Command Authoring](authoring-command.md) or
[Skills Authoring](authoring-skills.md). It describes only the shared input contract.

## Where elicitation applies

Declare `elicitation` only on an interactive command or the selected `SKILL.md` entrypoint.
Guide resolves it before rendering the body. A command supports native command resources,
`guide://_command` resource reads, and underscore, colon, and semicolon prompt routes. A skill
supports its selected `guide://$skill-name` entrypoint.

Ordinary documents and non-entrypoint skill members do not elicit. An entrypoint may also compose
forms from partials explicitly named by its `includes` frontmatter. A listed partial may contribute
frontmatter-only forms; its body still appears only when the entrypoint renders the normal Mustache
partial. `requires-*` is evaluated before a partial contributes its forms.

Form identifiers and field names must be unique across the effective entrypoint and its contributing
partials. Invalid frontmatter, duplicate identifiers or fields, self-references, and conditional
cycles are authoring errors.

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

Supported property types are `string`, `integer`, `number`, and `boolean`. `enum` values and
defaults must use the declared primitive type. `required` must name properties in that same form.
The MCP client receives the schema unchanged, apart from command-only dynamic properties described
below, so descriptive property metadata such as a title or description may improve the UI when the
client supports it.

### Command-only dynamic sources

Commands may use `source: workflow-phases` on a string property to derive an enum from the enabled
workflow phases before the form is delivered. The active phase is omitted from an interactive choice,
while an explicit positional or URI phase remains available for normal command validation. Guide
removes this command-only `source` marker before delivery. Skills do not perform command
specialisation and therefore must not use it.

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
obtain the missing information in its own instructions. An explicit decline remains a decline; it
does not silently apply defaults. Without a complete default or `fallback: render`, Guide returns
a validation failure naming the URI keywords the caller must supply.

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
form inapplicable. A condition whose value is not yet known makes the branch unresolved; Guide
first asks for the form that supplies that value, even if the supplier has no required fields.

Guide re-evaluates branches after each accepted answer, default, and cancellation. This supports
multi-step flows without asking for a branch that no longer applies. A form cannot depend on itself
or participate in a dependency cycle.

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
| Legacy MCP | Guide uses the legacy sequential elicitation request path and asks only the forms currently applicable. |
| MCP 2026-07-28 | Guide returns an `input_required` result containing the currently applicable forms. The client sends accepted responses on a later request. |

For the modern protocol, continuation state retains accepted values, completed forms, requested
forms, the originating entrypoint, the original URI keywords, and command positional arguments.
FastMCP seals this state before it reaches the client and unseals it before Guide receives the next
request. A changed or cross-entrypoint state is rejected before its values are used.

This is a framework integrity boundary, not an author-facing encryption feature: authors should
not place secrets in forms merely because continuation state is sealed. Treat all accepted values as
ordinary user input and use only the declared, validated primitive fields.

## Rendering accepted values

Accepted and normalised values are merged with command or skill keyword context. Use the ordinary
Mustache keyword paths for the entrypoint type, for example:

```mustache
Reviewing {{kwargs.mode}} {{kwargs.reference}}
```

The resolver never infers a form from an entrypoint name. It uses only the effective `elicitation`
frontmatter declared by the selected interactive entrypoint and its eligible partials.
