# Tasks: add-category-topics

## 1. Document Discovery

- [ ] 1.1 Implement `discover_category_documents(category, pattern)` — queries both filesystem
      template corpus and stored project documents for a category; returns raw document paths
      without rendering; respects `_` prefix exclusion
- [ ] 1.2 Write unit tests for `discover_category_documents` covering: filesystem-only, stored-only,
      combined results, `_` prefix exclusion, empty results

## 2. Sub-path Filtering

- [ ] 2.1 Extend `get_category_content` delegation chain to detect a trailing slash in the document
      pattern as the sub-path filter signal
- [ ] 2.2 Implement prefix-filter semantics: narrow documents matched by existing project patterns
      to those under the sub-path prefix (do not override patterns)
- [ ] 2.3 Write unit tests covering: trailing slash detection, prefix narrowing, interaction with
      existing patterns, no-trailing-slash unchanged behavior

## 3. Partial Machinery Refactoring

- [ ] 3.1 Identify shared document-fetching logic between existing partial resolution and the new
      policy pre-rendering path
- [ ] 3.2 Extract into `discover_category_documents` (from task 1.1) so both code paths use the
      same function
- [ ] 3.3 Verify existing partial resolution tests still pass after refactoring

## 4. Policy Pre-rendering

- [ ] 4.1 Parse `policies:` frontmatter key in templates (list of topic strings)
- [ ] 4.2 For each declared topic, call `discover_category_documents` on the `policies` category
      with sub-path filtering for that topic
- [ ] 4.3 Pre-render each matched document as a mustache partial with context:
      `policy_topic`, `policy_category`, `policy_path`
- [ ] 4.4 Merge frontmatter from policy documents using the same rules as regular partial
      frontmatter (combined, deduplicated — not stripped)
- [ ] 4.5 Register pre-rendered content as a mustache partial under the topic key
      (e.g. topic `git/ops` → partial key `git/ops`)
- [ ] 4.6 Write unit tests covering: single topic, multiple topics, per-document context vars,
      frontmatter merging, mustache partial registration

## 5. Missing Policy Placeholder

- [ ] 5.1 Define `INSTRUCTION_MISSING_POLICY` constant
- [ ] 5.2 Create `_missing_policy` system template (underscore prefix, not user-selectable)
- [ ] 5.3 When a declared policy topic resolves to zero documents, render `_missing_policy` as
      the partial content
- [ ] 5.4 Write unit tests covering: no-match → placeholder rendered, placeholder content contains
      INSTRUCTION_MISSING_POLICY

## 6. Guide URI Resolution

- [ ] 6.1 Wire `guide://policies/<topic>` URI to resolve via sub-path filtering of the `policies`
      category (trailing slash appended internally if needed)
- [ ] 6.2 Concatenate all matched documents (composable resolution — no exclusivity logic in
      resolver)
- [ ] 6.3 Return `_missing_policy` placeholder when no documents match the topic
- [ ] 6.4 Write integration tests covering: active policy resolves, no policy → placeholder,
      multi-document composable topic

## 7. Validation

- [ ] 7.1 `openspec validate add-category-topics --strict --no-interactive`
- [ ] 7.2 `uv run ty check src/`
- [ ] 7.3 `uv run pytest -q`
