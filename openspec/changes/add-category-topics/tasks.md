# Tasks: add-category-topics

## 1. Document Discovery / `_` prefix exclusion

- [x] 1.1 `_` prefix exclusion added unconditionally to `gather_category_fileinfos`
      (filesystem files with any path component starting with `_` are excluded;
      stored documents are exempt — they are deliberately user-imported)
- [x] 1.2 Tests in `tests/unit/test_mcp_guide/content/test_gathering.py`
      covering: root `_INDEX.md` excluded, `_system/` dir excluded, nested `_notes.md`
      excluded, stored docs with `_` prefix NOT excluded

## 2. Sub-path Filtering

- [x] 2.1 Trailing slash in passed pattern detected in `gather_category_fileinfos`
      as sub-path filter signal (not a pattern override)
- [x] 2.2 Prefix-filter semantics: category's configured patterns filtered to those
      starting with the trailing-slash prefix; discovery runs with filtered patterns
- [x] 2.3 Tests covering: matching patterns kept, non-matching discarded,
      no matches → empty, no trailing slash → unchanged override behaviour,
      multiple matching patterns all used

## 3. Partial Machinery Refactoring

- [x] 3.1 No separate refactoring required — `_gather_policy_partials` uses
      `gather_category_fileinfos` which already handles both filesystem and stored
      documents. Existing partial machinery (filesystem `includes`) is unchanged.
- [x] 3.2 Existing partial resolution tests confirmed passing throughout

## 4. Policy Pre-rendering

- [x] 4.1 `_gather_policy_partials(file_info, template_context, base_dir, project_flags)`
      implemented in `content/utils.py`; parses `policies:` frontmatter key via
      `parse_content_with_frontmatter` (deferred import of `gather_category_fileinfos`
      to avoid circular dependency)
- [x] 4.2 For each topic, calls `gather_category_fileinfos` with trailing-slash sub-path filter
- [x] 4.3 Each matched document rendered via `render_template` with context:
      `policy_topic`, `policy_category`, `policy_path`
- [x] 4.4 Policy document frontmatter handled by `render_template` pipeline
      (same rules as regular partial frontmatter — not stripped)
- [x] 4.5 Pre-rendered content registered in `pre_partials` dict keyed by topic;
      passed to `render_template` via new `pre_partials` parameter
- [x] 4.6 `render_template` extended with `pre_partials: dict[str, str] | None = None`
      parameter; passed through to `render_template_content` as `partials=`
- [x] 4.7 `read_and_render_file_contents` calls `_gather_policy_partials` before
      `render_template` for each template file
- [x] 4.8 Tests in `test_gathering.py` and `test_render_template.py`

## 5. Missing Policy Placeholder

- [x] 5.1 `INSTRUCTION_MISSING_POLICY` constant added to `result_constants.py`
- [x] 5.2 `_missing_policy.md` system template created in `templates/_system/`
- [x] 5.3 `render_missing_policy(topic) -> str` utility in `content/utils.py`;
      returned by `_gather_policy_partials` when a topic has no matching documents
- [x] 5.4 Tests: placeholder contains constant, contains topic name,
      different topics produce distinct output, no-match case in `_gather_policy_partials`

## 6. Guide URI Resolution

- [x] 6.1 `guide://policies/<topic>` handled in `resources.py`: when `collection == "policies"`
      and `document` is non-empty, a trailing slash is appended to `document` before
      passing as `ContentArgs.pattern`; triggers sub-path filtering in step 2
- [x] 6.2 Composable resolution: all matched documents concatenated by existing pipeline
- [x] 6.3 No-match case returns empty result (placeholder not injected at URI layer —
      that is a template-level concern)
- [x] 6.4 Integration tests in `tests/integration/test_resource_handlers.py`
      covering: trailing slash injected for topics, no injection for empty document

## 7. Validation

- [x] 7.1 `openspec validate add-category-topics --strict --no-interactive` — valid
- [x] 7.2 `uv run ty check src/` — all checks passed
- [x] 7.3 `uv run pytest -q` — 1778 passed (19 new tests, no regressions)
