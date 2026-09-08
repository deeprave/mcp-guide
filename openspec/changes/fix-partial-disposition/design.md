## Context

See proposal.md for motivation. The renderer already tracks ordinary partial names that Chevron actually expands, but retains their frontmatter only for instruction composition. Policy-topic documents are rendered before the parent and passed into Chevron as text-only partials, losing all frontmatter before the renderer can decide which policy topics were used. Existing template-rendering requirements already require policy frontmatter to be merged under the same rules as regular partials.

## Goals / Non-Goals

**Goals:**

- Make disposition composition explicit, conservative, and based only on content that reaches the rendered result.
- Apply one consistent partial-contributor model to ordinary includes and `policies:` partials.
- Preserve the resolved disposition through the existing delivery paths that consume rendered content.

**Non-Goals:**

- Change disposition precedence or frontmatter instruction semantics.
- Redesign policy discovery, Mustache syntax, or client response metadata.
- Fold cache-policy work into this change; cache composition remains the separate `add-cache-settings` review action.

## Decisions

### Represent pre-rendered partials as content plus resolved metadata

Policy pre-rendering will retain the rendered text together with contributor metadata, rather than passing a bare string through the boundary. The template renderer will continue to give Chevron text, while its accessed-partial tracking selects the metadata of only the named partials it expanded.

This reuses the established distinction between available and rendered ordinary partials. Passing only strings was considered but rejected because metadata cannot be recovered after rendering and would leave disposition dependent on a second, divergent lookup.

### Resolve disposition once from actual contributors

The parent and all accessed contributor types will be passed to the established disposition-precedence resolver. The resulting value will be stored on rendered content or otherwise returned through the existing rendering result boundary. Consumers must use that resolved value instead of recomputing a parent-only disposition.

This keeps precedence centralised. Allowing each prompt, command, content, or status path to inspect partial frontmatter was rejected because it would duplicate selection logic and create inconsistent output handling.

### Preserve existing instruction composition

The change will extend the contributor data used for disposition without changing instruction override, deduplication, or defaulting rules. Existing instruction tests remain regression coverage; new tests focus on observable output disposition.

## Risks / Trade-offs

- [Contributor metadata is retained for an unused partial] → Consult only metadata associated with renderer-tracked accessed partials.
- [Policy topics contain several documents] → Associate all contributors with their topic and aggregate each contributor only when that topic is rendered.
- [A downstream path recomputes disposition from parent frontmatter] → Trace content, prompt, command, and status result creation and add end-to-end behavioural coverage.

## Migration Plan

No stored-data migration is required. Deploy as a rendering behaviour correction; a rollback restores the prior parent-only disposition handling.
