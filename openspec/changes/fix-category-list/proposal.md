# Proposal

## Why

A category can legitimately exist in project configuration and in the document store without a matching directory in the docroot. This is expected wherever documents are ingested into a user-defined category. File discovery currently treats the absent directory as an error, which breaks every operation on such a category:

- `category_list_files` without a `source` filter fails with `unhandled errors in a TaskGroup (1 sub-exception)`: the `FileNotFoundError` is raised inside the concurrent files/store task group, cancels the store lookup, and is wrapped in an `ExceptionGroup`. The stored documents are never returned.
- `category_list_files` with `source: files` leaks the raw `Base directory not found: <path>` error.
- Content gathering through the same `discover_documents` path is exposed to the same failure for these categories.

A missing category directory is not an error and must never be visible to the caller or reach the task group.

## What Changes

- Filesystem discovery (`discover_document_files`) no longer raises when the base directory does not exist or is not a directory. It skips the filesystem search and returns an empty result, as though no files matched.
- Combined discovery (`discover_documents`) therefore proceeds to the document store regardless of the directory, and returns whatever the store holds for the category. If neither source has anything, the result is empty.
- `category_list_files` needs no special handling: all three `source` modes return an empty list or the stored documents without error.
- Existing failures that are real errors (a relative base path, invalid patterns, permission errors on an existing directory) keep raising as before.
- Tests that assert `FileNotFoundError` for a missing base directory are updated to assert the empty result; new tests cover store-only and mixed categories.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `file-discovery`: filesystem discovery of a non-existent base directory yields no files instead of an error.
- `category-tools`: `category_list_files` lists stored documents for a category that has no directory in the docroot.

## Impact

- `src/mcp_guide/discovery/files.py` (`discover_document_files`).
- Callers of `discover_document_files`, whose behaviour for a missing directory changes from exception to empty result: `content/gathering.py`, `tools/tool_category.py`, `tools/tool_resource.py` (skills), `discovery/commands.py`, `prompts/guide_prompt.py`, `render/rendering.py`. Each already handles an empty result (see design.md).
- Tests under `tests/unit/test_mcp_guide/discovery/` and category tool tests.
- Not breaking at the API level; no new dependencies.

## Assumptions

- "Category list" is taken to mean the `category_list_files` failure observed against the `openspec` category. `category_list` itself works.
- "Return None" for a store with nothing for the category is implemented as an empty result (the existing `FileInfoList` return type), not a literal `None`.
