## Context

Guide needs a compact way for rendered instructions to point agents towards a
relevant Guide capability. The recommendation belongs to the rendered document,
not to result transport or task-management state.

## Decisions

### Render recommendations as part of the document

`recommend` records only values explicitly authored by a template. After the
template body renders, the document renderer classifies each value and appends
its compact JSON footnote before returning the document. No later layer knows
that the document contains recommendations.

The supported explicit forms are `skill:<name>`, `command:<name>`,
`content:<name>`, and `tool:<name>`. An unprefixed value means `content:<name>`.
The visible text uses the relevant Guide noun, while the footnote contains the
URI and, where applicable, the configured tool call. Skill footnotes include
the effective catalogue description.

### Keep all template surfaces on the normal pipeline

The helper is registered in the common template context. The renderer uses the
same full context when it evaluates partial requirements, merging resolved
project flags with the template context instead of replacing it. This means
skills, commands, content, workflow documents, and instruction templates all
receive the same rendering behaviour.

### Provide a narrow `use_skill` tool

`{{tool_prefix}}use_skill` is a project-dependent `@toolfunc` for clients that
cannot yet invoke Guide skills natively. It accepts one exact catalogue skill
identifier, optionally with `$`, and an `args` list. The shared command parser
receives `[skill_name, *args]`, so bare tokens become truthy keyword flags,
`no-*` tokens become false flags, and `key=value` values become keyword values.
It resolves only `SKILL.md`; skill package members remain resource-only.

## Trade-offs

- A footnote is deliberately part of the rendered text, so old clients can use
  the URI fallback without metadata support.
- Recommendation values are explicit template authoring input; the renderer
  does not scan prose for capability names.
- The compact option-token interface supports flags and key/value settings,
  rather than arbitrary positional arguments. Skills that need named values
  use `key=value`.
