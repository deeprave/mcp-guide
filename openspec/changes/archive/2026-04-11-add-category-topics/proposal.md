# Change: Add Category Topic Filtering and Policy Pre-rendering

## Why

The `add-policy-selection` change created a `policies` category with 71 documents organized by topic
(e.g. `policies/git/ops/`, `policies/testing/`). That corpus is now in place, but the system cannot
yet use it because two related capabilities are missing:

1. **Sub-path filtering in category content resolution.** `get_category_content` currently matches
   against the project's configured patterns, but it has no way to scope results to a sub-path of
   the category (e.g. "only documents under `git/ops/`"). Without this, `guide://policies/git/ops`
   cannot be resolved to the active policy for that topic.

2. **Policy includes in mustache templates.** Templates need a way to declare which policy topics
   they depend on (e.g. `policies: [git/ops, testing]`) and reference the resolved content inline
   via mustache partials (e.g. `{{> git/ops}}`). This requires a pre-rendering step that resolves
   each topic against the user's active patterns before the main template renders.

Both capabilities share a lower-level need: discovering category documents from both the filesystem
template corpus AND stored project documents, without going through the full rendering pipeline.
The partial machinery already handles filesystem documents; it needs to be extended to cover stored
documents and to share that discovery code with policy pre-rendering.

Additionally, when a template declares a policy topic dependency but no policy is selected for that
topic, the system should render a clear informational placeholder rather than silently dropping the
section.

## What Changes

### 1. `discover_category_documents` — dual-source document discovery

A new lower-level function `discover_category_documents(category, pattern)` that:

- Queries both the filesystem template corpus AND stored project documents for a category
- Returns document paths without going through the full rendering pipeline
- Respects `_` prefix exclusion (files and directories with `_` prefix are excluded)
- Is used as the shared foundation for partial resolution and policy pre-rendering

This is intentionally lower-level than `internal_get_category_content`, which does full rendering.

### 2. Sub-path filtering in `get_category_content`

Extend `get_category_content` (and its internal delegation chain) to support sub-path topic
filtering:

- A trailing slash in the document pattern is the primary signal for sub-path filtering
  (e.g. `pattern="git/ops/"`)
- Sub-path filtering uses prefix-filter semantics: it narrows the set of documents matched by the
  project's existing configured patterns, rather than overriding them
- Without a trailing slash, existing behavior is unchanged (pattern matching against configured
  patterns)

### 3. Policy include pre-rendering in mustache templates

Templates may declare policy topic dependencies in frontmatter:

```yaml
policies:
  - git/ops
  - testing
```

Before the main template renders, the system pre-renders each declared topic as a mustache partial:

- Topic is resolved against the `policies` category using the project's active patterns and
  sub-path filtering
- Each matched document is pre-rendered individually with per-document context variables:
  - `policy_topic` — the declared topic name (e.g. `git/ops`)
  - `policy_category` — the category containing the document (always `policies`)
  - `policy_path` — the relative path of the matched document
- The rendered content is registered as a mustache partial under the topic key (e.g. `git/ops`)
  so templates can reference it with `{{> git/ops}}`
- Frontmatter from policy documents is merged using the same rules as regular partial frontmatter
  (combined and deduplicated, not stripped)

### 4. Missing policy placeholder

When a template declares a policy topic but no document is selected for it:

- The system renders a `_missing_policy` system template as the partial content
- The rendered placeholder contains an `INSTRUCTION_MISSING_POLICY` constant value
- This is informational — it tells the AI assistant that no policy has been selected for the topic
  and it should proceed without one, not that the template is broken

### 5. Partial machinery refactoring

The existing partial resolution code (which handles `{{> partial-key}}` for filesystem partials)
shares the same document-fetching concern as policy pre-rendering. Refactor to:

- Extract shared discovery logic into `discover_category_documents`
- Ensure both partial resolution and policy pre-rendering use the same code path for locating
  documents, so that stored documents are not excluded from either

### 6. `guide://policies/<topic>` URI resolution

Wire the `guide://policies/<topic>` URI pattern to resolve via sub-path filtering of the `policies`
category:

- `guide://policies/git/ops` resolves all documents matching the project's active patterns under
  `policies/git/ops/`
- The resolver concatenates all matches (composable by default); exclusivity is the user's concern
- If no policy is selected for the topic, returns the `_missing_policy` placeholder

## Impact

- Affected specs:
  - `template-rendering` — policy pre-rendering, missing policy placeholder, partial refactoring
  - `category-tools` — sub-path filtering, discover_category_documents
  - `mcp-resources-guide-scheme` — guide://policies/<topic> resolution
- Affected code:
  - `src/mcp_guide/resources.py` — guide:// URI handler
  - `src/mcp_guide/rendering/` (or equivalent) — template rendering, partial resolution
  - `src/mcp_guide/categories.py` (or equivalent) — category content resolution
