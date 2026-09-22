## Context

Templates currently use `TemplateFunctions` to collect `_error` signals, then
carry those through `RenderedContent`. Startup delivery queues plain instruction
strings, and MCP adapters already place modern side-band values under the
`mcp-guide` metadata namespace. See proposal.md and the delta specifications.

## Goals / Non-Goals

**Goals:**

- Let a template recommend the next Guide item without adding recommendation
  prose to its rendered content.
- Preserve recommendations through normal rendering and every public response
  surface.
- Advertise effective Guide skills at startup only for the existing opt-in
  `mcp-skills` experiment.

**Non-Goals:**

- Infer user intent or automatically invoke a recommended item. The client
  chooses whether to retrieve a recommended Guide skill.
- Validate, execute, or install a recommended skill, tool, document, or
  expression.
- Replace the existing skill catalogue, its `usage` metadata, or the negotiated
  `skills/list` extension.

## Decisions

### Collect explicit rendered recommendation forms with a template lambda

`recommend` follows the `_error` pattern: it renders the enclosed Mustache
text, records its non-blank value on `TemplateFunctions`, and returns an empty
string. Its content is an explicit recommendation form, rather than arbitrary
prose to infer from. A Guide skill uses the form `Guide skill "<name>"`; its
structured item carries the skill name and a `guide://$<name>` resource
fallback. Other forms remain available for a tool, document, or expression.

This does not require the renderer to validate that a named skill currently
exists. It gives clients a stable, intention-rich name while retaining the URI
for clients, agents, and scripts that consume skill resources directly.

### Make Guide-skill references client-driven during transition

When a template directs an agent to a Guide skill, it records `Guide skill
"<name>"` through `recommend`. The resulting structured item makes the skill
name the primary client action. A future MCP `use_skill` tool receives that
name without a `$` prefix; until then, a client may resolve the item's
`guide://$<name>` resource fallback. The server neither recursively renders nor
invokes the selected skill. This provides the interim path for Git workflow
templates before they are refactored around recommendation items.

The template may retain a fluent visible instruction such as “Use the Guide
skill `git-commit`”. Where a visible resource reference is useful, it uses a
footnote-style reference rather than embedding the URI in the sentence. The
footnote contains the same fallback URI as the structured item. Recommendation
capture remains explicit: response rendering does not parse arbitrary prose
for skill names.

### Carry recommendations beside errors and instructions

Add an ordered `recommendations` collection to `RenderedContent`, sourced from
the `TemplateFunctions` instance. Rendering aggregation preserves each
contributor's recommendation order. A Guide-skill item is structured as a
named skill and its resource fallback, rather than a bare URI.

Result construction and MCP adapters promote a non-empty list to
`_meta["mcp-guide"]["recommendations"]`. This is independent of the existing
scalar instruction channel: an instruction explains state, while a
recommendation identifies a potential next item. Empty values do not create an
empty metadata namespace or key.

### Use a feature-gated startup partial for structured suggestions

`_startup` includes a dedicated partial with `requires-mcp-skills: true` in
its frontmatter. That partial owns the small, contextual selection of Guide
skills and declares them through the named Guide-skill recommendation form.
Normal partial requirement filtering omits it when the global experiment is
disabled, so the startup listener continues to queue only the rendered startup
result and does not grow a feature-flag branch.

Startup delivery maps the partial's recommendation items to the structured
`suggested_guide_skills` value. The partial makes suggestions discoverable; it
does not imply that the receiving client negotiated or implements `skills/list`.

### Keep recommendation authoring explicit and contextual

Templates add `{{#recommend}}…{{/recommend}}` only at a real action boundary.
The helper does not add generic recommendation boilerplate or make unrelated
features visible. This preserves the focused behaviour of status and other
read-only responses.

## Risks / Trade-offs

- [Clients ignore unknown metadata] → Text responses and existing catalogue
  access remain unchanged; capable clients can progressively adopt the field.
- [A recommendation is stale after a project change] → Startup derives its
  suggestions from the bound session's effective catalogue, and normal
  recommendation authors remain responsible for contextual placement.
- [Named item may not be available to a client] → Clients can use their
  available skill mechanism, including the resource fallback; the renderer
  does not falsely claim the skill was invoked.

## Migration Plan

The metadata is additive. Existing clients continue to receive their current
text and instruction fields, while clients that understand recommendations can
begin consuming the new keys. Removing the helper or ignoring the metadata is
safe rollback behaviour.
