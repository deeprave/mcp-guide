# Design: Add Policy Selection

## Purpose

This change separates optional operational preferences from the system's core guidance.

The key design goal is:

```text
keep principles broadly applicable
move preferences into selectable policy documents
```

## Core Model

The system already has the right storage primitives:

- categories
- collections
- profiles
- project configuration
- guide resource resolution

This change uses those primitives rather than inventing a new policy object type.

Under this design:

```text
core guidance
  = neutral, broadly applicable material

policy guidance
  = optional, topical variants that express user-selectable preferences
```

Policies remain ordinary documents or templates under a default `policy` category.

## Policy Organization

Policies should be grouped by topic rather than by one giant flat list.

Examples:

```text
policy/git/allow-commit
policy/git/disallow-commit
policy/workflow/full-phases
policy/workflow/simple-flow
policy/testing/strict
policy/testing/minimal
```

Not every topic will be binary. Some topics may have:

- multiple qualitative options
- layered options
- or topic-specific variants that are not cleanly expressible as allow/disallow

So the design should not require a fixed two-state policy model.

## Selection Model

The system needs to distinguish:

- all available policy documents for a topic
- the active policy selection for that project

This should be expressed using existing project configuration mechanisms rather than a parallel policy database.

The intended direction is:

```text
policy category
  stores policy variants

collections / profile additions / project config
  determine which policy variants are active
```

That keeps policy selection compatible with the rest of the document-composition model.

## Selected Policy Resolution

The eventual user experience should allow a reference like:

```text
guide://policy/scm
```

to resolve to the selected applicable policy material for that topic.

That implies a resource-resolution rule:

```text
topic request
  -> determine active policy selection for topic
  -> resolve selected policy content
```

This is preferable to exposing every alternative at once because policy topics are only useful when the system can reflect the user's chosen stance.

## Extraction Strategy

This change should not try to redesign the entire document corpus at once.

A practical first pass is:

1. audit the current user-facing templates and markdown documents
2. identify embedded optional preferences
3. extract the highest-value preferences first
4. replace embedded opinionated guidance in core docs with:
   - neutral guidance, or
   - references to policy topics where appropriate

The audit should prioritize:

- git / scm
- commit / pr behavior
- workflow strictness
- testing and type-checking posture
- toolchain / package manager expectations
- review and autonomy boundaries

Additional topics discovered during the audit remain in scope where they clearly represent optional preferences.

## Relationship to Guided Onboarding

This change intentionally stops at:

- defining policy material
- organizing it
- making it selectable and resolvable

It does not yet implement the interactive onboarding UX that helps users choose policies and other configuration options.

That follow-on change will consume the model created here.

## Rationale

This design is preferable to keeping policies embedded in core documents because it:

- reduces hidden author bias in the default experience
- makes project customization more visible
- keeps configuration aligned with existing categories/collections/profiles
- creates a clean foundation for guided onboarding later
