# Guide Skill Authoring

Guide skills are server-owned, native-skill-shaped packages in the configured document root:

```text
_skills/
  workflow-review/
    SKILL.md.mustache
```

The public entrypoint for that example is `guide://$workflow-review`. A skill package may include
`references/`, `scripts/`, or `agents/` members, which are retrieved individually through the same
skill URI root. `SKILL.md` is the entrypoint and contains the instructions an agent follows.

## Skill Frontmatter

Every skill entrypoint declares at least `name`, `description`, and `usage` in YAML frontmatter:

```yaml
---
name: workflow-review
description: Review a selected change and present the findings.
usage: Use when the user asks to review a change.
---
```

The normal document frontmatter fields, including `type`, `instruction`, `requires-*`, `cache`,
and template variables, apply to skills. Bundled skills omit `type`; their entrypoint delivery
defaults to `agent/instruction`.

## Elicitation

An entrypoint may declare MCP input forms under `elicitation`. Guide uses the declaration before
rendering the entrypoint when its required URI keywords are absent:

```yaml
---
name: workflow-review
description: Review a selected change.
usage: Use when the user asks to review a change.
elicitation:
  review-target:
    message: Choose the target for this code review.
    schema:
      type: object
      properties:
        mode:
          type: string
          description: "Review target: uncommitted, main, a branch name, a pull-request URL or reference, or a pull-request number"
      required: [mode]
---
```

Form identifiers are package-local. A declaration may contain multiple forms, but their property
names must not overlap. Each form must provide a non-empty `message` and an object `schema` with a
non-empty `properties` mapping. Supported property types are `string`, `integer`, `number`, and
`boolean`; `enum` values must be primitive values. Required property names must be declared in the
same form.

Guide never infers a form from a skill name. The selected `SKILL.md` frontmatter is the sole source
of the declaration.

When a client supports MCP elicitation, missing required properties produce the declared MCP form.
The accepted primitive values are made available to the entrypoint as normal template keywords. An
entrypoint can instead supply them directly in its URI:

```text
guide://$workflow-review?mode=main
guide://$workflow-review?mode=feature/example
```

Provided URI values take precedence for the corresponding properties and avoid requesting that
form. `false` and `0` are valid supplied values; only omitted, null, or blank string values leave a
required property unresolved. A property may use its standard JSON Schema `default` as a safe
fallback when the client cannot elicit, or when the user cancels the form. Every required property
in the form must have a valid default for this fallback to apply. An explicit user decline remains a
decline rather than applying the default. The rendered template can inspect
`{{#elicitation.defaulted.<form-name>}}` to explain that it is using a default. If a form does not
provide complete defaults and the client cannot elicit, Guide returns an error naming the required
keywords so the caller can supply them explicitly.

Alternatively, set `fallback: render` on the form to render the entrypoint without unresolved
values when elicitation is unavailable or cancelled. Use this when the skill's instructions can
obtain the missing value directly from the user. An explicit user decline remains a decline.

### Scope

`elicitation` is available only on the selected root `SKILL.md` entrypoint of a Guide skill package.
It is not evaluated for ordinary documents, command templates, partials, or skill package members
such as `references/`, `scripts/`, and `agents/`. Those rendering paths do not own an MCP
request/response interaction and therefore cannot safely create an input request.

The accepted values are added to `kwargs` and `raw_kwargs` using the same context model as command
URI query arguments. Use standard Mustache expressions such as `{{kwargs.mode}}` and
`{{kwargs.reference}}` in the entrypoint.

## Security and Execution

Scripts are delivered as content only. Guide does not execute a script from a skill package. A
client that chooses to download and execute one does so locally and must treat it as untrusted until
it has been inspected.
