## Why

Guide skill entrypoints can already declare capability-negotiated MCP input forms in
frontmatter, but command templates cannot use the same interaction. Commands are a
natural interactive surface, and the existing flat form model cannot express a
follow-up question whose applicability depends on an earlier answer. Partials also
cannot contribute input requirements despite already contributing other rendered
document properties.

## What Changes

- Extend the shared, frontmatter-declared elicitation mechanism to Guide command
  templates without command-name-specific routing or a second implementation.
- Add declarative branching so a form can become applicable after prior URI or
  elicited values meet its declared condition, requesting a follow-up form only
  when needed.
- Allow rendered partials to contribute elicitation declarations to their parent,
  combining distinct forms with the parent and other contributing partials.
- Support frontmatter-only partials that contribute properties, including
  elicitation, without emitting document interpolation content.
- Preserve direct document delivery as a non-interactive serving path; it does
  not evaluate elicitation declarations.
- Document the authoring contract, branching lifecycle, partial composition, and
  command support in developer documentation.

## Capabilities

### New Capabilities

- `template-elicitation`: Declarative MCP input forms shared by skill and command
  entrypoints, including conditional follow-up forms and composed partial
  contributions.

### Modified Capabilities

- `mcp-resources-guide-scheme`: Command URI execution can return and resume a
  capability-negotiated elicitation before rendering the command.
- `template-rendering`: Rendered partial frontmatter contributes elicitation
  declarations, including property-only partials that render no body content.

## Impact

- Affected code: shared elicitation resolver, command dispatch and resource
  handling, frontmatter/document-property composition, partial rendering, and
  request-context propagation.
- Affected templates: command templates and rendered partials may opt into the
  new frontmatter contract; ordinary document delivery remains unchanged.
- Affected documentation: developer skill, command, and template authoring
  guidance.
