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

- Supply concise, practical `jinja2` and `chevron` language guidance.
- Make each profile independently selectable and composable with the existing
  language, framework, and testing profiles.
- Document template-language profiles in the user profile catalogue.
- Validate profile discovery and real project application behaviour.

**Non-Goals:**

- Adding a Jinja2, Mustache, or Chevron renderer to Guide.
- Selecting a renderer from project configuration or inferring one at runtime.
- Defining guidance for every template language in this change.
- Reworking profile storage, profile discovery, or onboarding mechanics.

## Decisions

### Use one profile and one `lang/` document per template language

Add `jinja2.yaml` and `chevron.yaml`, each selecting exactly its matching
`lang/` document. This is consistent with the existing language-profile shape,
keeps application idempotent, and makes a future language a small, isolated
addition.

The alternative—a generic template profile containing all template guidance—was
rejected because it would give an agent conflicting syntax and escaping advice
when only one engine is used.

### Treat Chevron as Mustache-family guidance

The `chevron` document will identify Chevron as a Python implementation of
Mustache and cover Mustache syntax, sections, inverted sections, partials,
escaping, and the absence of arbitrary expression evaluation. It will name the
profile after the engine users select in Guide rather than creating a second,
overlapping `mustache` profile.

### Keep documents concise and action-oriented

Each language document will give an AI a crash course: basic syntax, control
flow and composition, auto-escaping and safe-data rules, whitespace/partial
pitfalls, and behaviour-focused validation. It will link to authoritative
language documentation where that helps, rather than duplicating a language
reference.

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

1. Package the two new profile YAML files and language documents.
2. Update the profile catalogue documentation.
3. Add behavioural coverage that applies each profile to a project and confirms
   the corresponding language guidance is selected once.
4. Existing projects remain unchanged until a user applies a new profile; no
   migration or rollback action is required.
