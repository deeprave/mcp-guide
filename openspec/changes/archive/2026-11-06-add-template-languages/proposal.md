# Proposal

## Why

Guide profiles currently supply language and framework guidance, but offer no
focused help when a project uses a template syntax or code-first markup DSL.
Agents therefore receive neither a concise language outline nor links to the
authoritative reference needed to edit templates confidently.

## What Changes

- Add bundled, selectable, additive profiles and concise `lang/` guidance for
  the agreed template syntaxes: Mustache, Handlebars, Jinja2, Django Templates,
  Mako, Chameleon, Velocity, Thymeleaf, FreeMarker, JTE, kotlinx.html, Go
  templates, templ, Jet, Pongo2, Askama, Tera, MiniJinja, handlebars-rust,
  Maud, JSX/TSX, Nunjucks, EJS, Pug, Blade, Twig, Latte, ERB, Slim, Haml,
  Liquid, Leaf, Stencil, Razor, Scriban, StringTemplate, Pebble, Qute, Smarty,
  Ructe, Yarte, gomponents, and inja.
- Make Mustache generic rather than implementation-specific, and identify
  Chevron and other language implementations in its guidance.
- Add Django Templates automatically through the existing Django profile;
  keep every other template profile explicitly selected and non-exclusive.
- Give every guidance document a short, non-opinionated authoring checklist
  and primary reference URLs rather than a language tutorial.
- Make the profile catalogue documentation describe the new template-language
  profiles and their additive use alongside programming-language and framework
  profiles.
- Do not infer a template engine from file extensions, dependencies, or project
  layout, and do not add rendering/runtime dependencies to Guide.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `language-profiles`: Add bundled, additive template-language and markup-DSL
  profiles and their focused `lang/` guidance.
- `documentation`: Document the available template-language profiles and how
  they compose with other profiles.

## Impact

- Bundled profile definitions under `src/mcp_guide/templates/_profiles/`.
- Bundled language guidance under `src/mcp_guide/templates/lang/`.
- Profile catalogue documentation and profile discovery/onboarding coverage as
  required by the existing profile model.
- No template renderer, document format, external dependency, or configuration
  format change.
