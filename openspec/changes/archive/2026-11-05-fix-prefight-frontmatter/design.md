## Context

See proposal.md for motivation. `collect_interactive_document_properties` loads all eligible declared includes before inputs are resolved. It builds general `DocumentProperties`, exposes `delivery_properties`, and both command and skill dispatch merge these into rendered properties. This bypasses the ordinary renderer's tracking of actually rendered partials. Both `_workflow-setup-needed` and `_client-info` declare `agent/instruction`; their declarations leak into status even when body conditions skip them. Existing tests explicitly retain cache restrictions from preflight-only partials, conflicting with rendered-contributor semantics.

## Goals / Non-Goals

**Goals:** Establish one deterministic authority for response metadata; retain pre-render input resolution across all entrypoints; discard unrelated headers once preflight has extracted its required state.

**Non-Goals:** Change form schemas, prompting protocols, disposition precedence, cache combination rules, workflow availability conditions or ordinary Mustache partial rendering. This proposal does not implement the correction.

## Decisions

### Project preflight state onto input concerns

Preflight may temporarily read supporting variables and evaluate requirements to resolve form declarations. At the earliest boundary after extraction, retain only elicitation-related state and diagnostics, plus `requires-*` and `includes` if still required for eligibility or discovery. Use an explicit allowlist rather than a denylist, so future delivery properties cannot leak automatically. Do not mutate original source frontmatter or shared rendering context. The resolved inputs remain available to the later render.

Do not retain unrelated `type`, `instruction`, `description`, `cache` or arbitrary headers in the preflight result. Avoid evaluating unrelated renderable headers in preflight merely to discard them: their diagnostics or extensions could otherwise affect an input-only operation. Shared parsing machinery can remain, but only input-relevant evaluation belongs to preflight.

### Remove preflight delivery composition everywhere

Remove the delivery property carrier and its merge from commands and skills; audit every caller and shared helper. Preflight should not run solely to determine output properties. Ordinary rendering independently reads original frontmatter with the final resolved inputs and determines metadata from the parent and actual rendered contributors. This retains existing type precedence and cache restrictions when a partial actually renders.

Keeping explicit cache headers from form-only partials was considered and rejected: cache policy already has a rendering path and a form declaration is not a rendered output contributor. Authors who require an output restriction must declare it on the parent or an actual rendered contributor. No cache-specific preflight exception remains.

### Preserve shared form discovery

Declared includes remain discoverable for forms even without a body partial tag. Keep requirement filtering, source-aware diagnostics, duplicate detection, missing-partial behaviour and malformed-includes handling. This is a distinct input-discovery contract, not permission for those partials to contribute delivery headers.

## Risks / Trade-offs

- Existing tests or author expectations preserve form-only cache metadata → revise them and document that output restrictions belong on rendered contributors.
- Filtering too early removes context needed to resolve forms → preserve temporary evaluation context until input declarations are resolved, then discard unrelated state without modifying rendering inputs.
- Shared processing still evaluates unrelated headers → cover unrelated-header diagnostics and extension effects through observable preflight behaviour.
- Command and skill paths diverge → cover both entrypoints and audit all preflight consumers.
- Concurrent `fix-elicitation-forms` work changes the same files → inspect the current diff before implementation and preserve unrelated edits.

## Migration Plan

Update the shared boundary, remove delivery merges, revise behaviour tests and authoring guidance, and run focused checks followed by required project validation. No persisted data migration is needed. Rollback restores the previous code, but reintroduces metadata leakage.
