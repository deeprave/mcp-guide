# Tasks

## 1. Standard skills transport

- [ ] 1.1 Replace the private negotiated skills extension with the SEP-2640 `io.modelcontextprotocol/skills` capability and metadata-only `skills/list` and `skills/get` operations for modern clients, retiring the `mcp-skills` feature flag.
- [ ] 1.2 Serve effective Guide skill entrypoints and package members through stable dynamic `skill://` resource URIs by delegating selected reads to the shared Guide skill resolver without retaining rendered skill content.
- [ ] 1.3 Add the capability-aware `skill` template section, retain Guide URI delivery for legacy or non-negotiating clients, and emit one refresh notification when rebuilding detects an effective catalogue change.

## 2. Binding-aware discovery

- [ ] 2.1 Refactor skill metadata discovery so it loads frontmatter only, never renders templates or policies, and builds an unbound catalogue independently of project-specific requirement evaluation, including `project-bind: true` binding-only metadata.
- [x] 2.2 Make skills requiring only project binding discoverable before binding with concise binding guidance; suppress skills with additional unmet requirements until a bound refresh satisfies them.
- [ ] 2.3 Revise Git packages for complete unbound rendering, with policy partials resolving blank automatically when unbound and selected project policies resolving only when bound, and update the affected extension coverage.
- [x] 2.4 Add `depth` selection to the workflow-review skill and paired command: quick runs one lighter reviewer, standard runs one heavier reviewer, and thorough runs both independently before returning one combined review.
- [x] 2.5 Add `get_cache_dir()` as an implied runtime read/write root exposed through `{{path.cache}}` in bound and unbound contexts; cache bound reviews by project identity and issue, and unbound pull-request reviews and triage by canonical provider, repository, and pull-request identity.
- [x] 2.6 Provide unbound variants for triage-items, triage-review, and triage-pr: use supplied conversational inventories or review inputs, require an explicit pull-request identity for PR triage, and use the shared cache without migrating existing project review or triage artefacts.
