## Context

See proposal.md for motivation. The renderer already tracks ordinary partial names that Chevron actually expands, but retains their frontmatter only for instruction composition. Policy-topic documents are rendered before the parent and passed into Chevron as text-only partials, losing all frontmatter before the renderer can decide which policy topics were used. Existing template-rendering requirements already require policy frontmatter to be merged under the same rules as regular partials.

## Goals / Non-Goals

**Goals:**

- Replace the split document and partial aggregation paths with one typed properties model.
- Make disposition composition explicit, conservative, and based only on content that reaches the rendered result.
- Apply one consistent partial-contributor model to ordinary includes and `policies:` partials.
- Preserve the resolved disposition through the existing delivery paths that consume rendered content.

**Non-Goals:**

- Change disposition precedence or frontmatter instruction semantics.
- Implement instruction-property composition; the model will permit a later `DocumentInstruction` property without changing its current behaviour in this change.
- Redesign policy discovery, Mustache syntax, or client response metadata.
- Fold cache-policy work into this change; cache composition remains the separate `add-cache-settings` review action.

## Decisions

### Represent pre-rendered partials as content plus resolved metadata

Policy pre-rendering will retain the rendered text together with contributor metadata, rather than passing a bare string through the boundary. The template renderer will continue to give Chevron text, while its accessed-partial tracking selects the metadata of only the named partials it expanded.

This reuses the established distinction between available and rendered ordinary partials. Passing only strings was considered but rejected because metadata cannot be recovered after rendering and would leave disposition dependent on a second, divergent lookup.

### Use a shared, typed document-properties model

Each parent document, ordinary partial, policy partial, and collected delivery document will be represented by a `DocumentContribution`: rendered content, retained frontmatter where rendering requires it, and `DocumentProperties` derived from that frontmatter. `DocumentProperties` owns the frontmatter dispatch boundary and contains registered `DocumentProperty` handlers.

The initial handlers are `DocumentCache` and `DocumentDisposition`. When ingesting frontmatter, `DocumentProperties` SHALL offer every key and value to every handler; it SHALL not assume that a key belongs to only one handler or that a handler consumes only one key. Each handler owns its defaults and its domain-specific composition rules. The container combines the properties of the parent and actual contributors for both rendered partials and multi-document delivery.

This deliberately replaces, rather than wraps, the separate cache-policy and disposition aggregation paths, but is a packaging refactor: cache and disposition behaviour SHALL remain exactly as it is today. Runtime callers SHALL inject the existing contextual defaults and conditions where current paths already distinguish them, including the ordinary non-template Markdown cache default and the different template versus collected-content disposition defaults. Handlers SHALL NOT infer new policy from filenames or invent broader defaults. A future `DocumentInstruction` handler may consume `instruction`, `type`, and any further relevant keys through the same dispatch mechanism, but instruction composition is not changed by this change.

### Resolve properties once from actual contributors

The parent and all accessed contributor types will be combined into `DocumentProperties` once. Its `DocumentDisposition` handler will use the established disposition-precedence resolver, and its `DocumentCache` handler will retain the existing conservative cache rules. The resulting properties will be stored on rendered content or otherwise returned through the existing rendering result boundary. Consumers must use those resolved properties instead of recomputing a parent-only disposition or separately collating cache policy.

This keeps precedence centralised. Allowing each prompt, command, content, or status path to inspect partial frontmatter was rejected because it would duplicate selection logic and create inconsistent output handling.

### Preserve existing instruction composition

The change will extend the contributor data used for disposition without changing instruction override, deduplication, or defaulting rules. Existing instruction tests remain regression coverage; new tests focus on observable output disposition.

## Risks / Trade-offs

- [Contributor metadata is retained for an unused partial] → Consult only metadata associated with renderer-tracked accessed partials.
- [Policy topics contain several documents] → Associate all contributors with their topic and aggregate each contributor only when that topic is rendered.
- [A downstream path recomputes disposition from parent frontmatter] → Trace content, prompt, command, and status result creation and add end-to-end behavioural coverage.
- [A new property needs several frontmatter keys] → Broadcast keys to property handlers rather than assigning ownership in `DocumentProperties`.

## Migration Plan

No stored-data migration is required. Deploy as a rendering behaviour correction; a rollback restores the prior parent-only disposition handling.
