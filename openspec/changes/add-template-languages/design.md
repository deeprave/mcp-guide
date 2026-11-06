# Design

## Context

Profiles are data files that add patterns to existing project categories. The
installed catalogue discovers profile YAML files dynamically, so a language
profile needs no registry or runtime code. Bundled language guidance is rendered
from `src/mcp_guide/templates/lang/` and selected by a profile's `lang`
patterns.

The profile system already treats selections as additive and idempotent. The
new guidance must fit that model: it informs an agent how to work with template
files, but does not alter Guide's own Mustache rendering implementation.

## Goals / Non-Goals

**Goals:**

- Supply concise, practical guidance for the agreed template syntaxes and
  code-first markup DSLs.
- Make every template profile independently selectable and composable with the
  existing language, framework, and testing profiles, except that Django adds
  its own Django Templates guidance automatically.
- Document template-language profiles in the user profile catalogue.
- Validate profile discovery and real project application behaviour.

**Non-Goals:**

- Adding a Jinja2, Mustache, or Chevron renderer to Guide.
- Selecting a renderer from project configuration or inferring one at runtime.
- Inferring a template engine from filenames, dependencies, or project layout.
- Reworking profile storage, profile discovery, or onboarding mechanics.

## Decisions

### Use one profile and one `lang/` document per distinct syntax

Each distinct syntax receives an independently selectable profile and matching
`lang/` document. The profiles are additive and idempotent, so a project can
select more than one engine without losing existing guidance. This avoids
conflicting syntax and escaping advice while retaining a small, repeatable
profile shape.

### Treat Mustache as a generic syntax

The `mustache` document covers the formal Mustache syntax and links to its
specification and implementation catalogue. Chevron is identified as a Python
implementation, not a separate syntax profile. Handlebars is separate because
its helpers, blocks, and escaping behaviour extend the Mustache family.

### Keep Django Templates distinct

Django Templates is distinct from Jinja2 even though Django can be configured
with different engines. The existing Django profile adds `django-templates`
guidance automatically; Jinja2 and all other template profiles remain explicit.

### Keep documents concise and action-oriented

Each guidance document gives an AI a short, non-opinionated editing checklist:
identify the configured engine and escaping mode, preserve the project's
composition and whitespace conventions, keep application logic out of templates
where the engine permits it, and validate rendered behaviour. Each document
links to the engine's primary reference rather than duplicating a language
tutorial. Code-first markup DSL documents explicitly identify that distinction.

### No renderer coupling

Profiles are project guidance only. Jinja2 guidance does not cause Guide to
render Jinja2 files, and Chevron guidance does not change how Guide renders its
own `.mustache` documents. This preserves the established profile boundary and
avoids introducing a runtime dependency merely to provide instructions.

## Risks / Trade-offs

- [Guidance becomes stale as an engine evolves] → Keep the documents short,
  version-neutral where possible, and link to primary documentation.
- [An agent applies an irrelevant profile] → Profiles remain explicitly
  selectable and additive; Guide does not infer a renderer from a filename in
  this change.
- [Future engines need different concerns] → The one-profile/one-document
  pattern accommodates engine-specific documents without changing the profile
  mechanism.

## Migration Plan

1. Package the agreed profile YAML files and matching language documents.
2. Wire Django Templates into the Django profile.
3. Update the profile catalogue documentation and primary references.
4. Existing projects remain unchanged until a user applies a template profile;
   no migration or rollback action is required.
