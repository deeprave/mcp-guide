# Design

## Context

See proposal.md. The current command and skill paths collect form declarations from the entrypoint and every declared frontmatter include before rendering. This means a form can be requested even when the template's own conditional branch would select different instructions.

## Goals / Non-Goals

**Goals:**

- Make form delivery follow the actual Mustache render path.
- Keep schemas in frontmatter and use the existing form validation, MCP capability negotiation, continuations, fallbacks, and keyword context.

**Non-Goals:**

- Changing the form schema subset, validation rules, protocol support, URI keyword semantics, or static document rendering.

## Decisions

### Rendered `elicit` section selects a declaration

Add an asynchronous `elicit` section extension to the per-render template extension registry. Its body names a form declared by the active template or rendered partial. Only reaching the section invokes its form. The extension awaits normal MCP form resolution, then renders its enclosed source with accepted values layered into the normal `kwargs` and `raw_kwargs` context.

This keeps the form declaration structural and reusable while making invocation ordinary template control flow. It replaces eager include-tree scanning, which cannot know which Mustache branch will render.

Forms resolve in the order their `elicit.<form-id>` sections are reached. A `when` dependency may therefore reference a URI value or a value accepted by an earlier invocation. Independent forms remain separate interactions; batching them would require a separate discovery pass and is outside this design.

### Render-order declaration replacement

The renderer maintains one request-local form registry. When a template or partial renders an `elicitation` mapping, it updates that registry; a later declaration with the same form identifier replaces the earlier one. Include declaration order has no effect. No scoped restoration or layered lookup is introduced.

## Risks / Trade-offs

- [A form can pause a render] → the asynchronous section extension awaits the established MCP interaction before rendering its enclosed content.
- [A form identifier can be ambiguous across rendered sources] → retain source-aware duplicate diagnostics for the actual invocation set.
- [Legacy clients may fall back instead of presenting a form] → preserve the existing fallback behaviour and render the enclosed section with the existing defaulted-form context.

## Migration Plan

1. Implement the `elicit` section extension and render-result invocation state.
2. Route command and skill interaction through rendered invocation rather than preflight collection.
3. Convert shipped interactive templates and form-bearing partials to explicit `elicit` sections.
4. Remove obsolete preflight collection code and frontmatter-only elicitation support.
5. Update developer documentation with the declaration and invocation pattern.

Rollback is a normal code revert; no persisted state or client migration is required.
