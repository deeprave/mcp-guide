# Proposal

## Why

Guide currently discovers elicitation declarations across a command or skill's frontmatter includes before rendering any template content. That can request input for a branch which the rendered template would not select.

## What Changes

- Make frontmatter `elicitation` declarations schemas only; they do not request input merely because their template or an included partial was discovered.
- Add a rendered `elicit` section extension. A template invokes a named declared form at the exact point and inside the conditional branch where its values are required.
- Resume rendering the enclosing section with accepted form values available in the normal template context.
- Replace preflight-only elicitation partial collection with rendered-template invocation, so only forms reached through the actual Mustache rendering path are applicable.
- Update developer guidance and convert shipped interactive templates to the rendered `elicit` pattern.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-elicitation`: Select and resolve declared forms only when a rendered template invokes them.
- `template-rendering`: Preserve render-path ordering while allowing a section extension to suspend for elicitation and resume with values.
- `guide-url-skills`: Expose parsed URI keywords through the single public `kwargs` template mapping.

## Impact

- Affects template rendering extensions, command and skill interactive delivery, shipped interactive templates, and developer guidance.
- Removes the current pre-render elicitation scan and its frontmatter-only partial behaviour.
- Does not change MCP form validation, protocol negotiation, URI keyword precedence, or the returned-value keyword context.
