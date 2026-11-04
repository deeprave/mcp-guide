# Design

## Context

See proposal.md - Why.

`discover_document_files` (`discovery/files.py`) raises `FileNotFoundError` when the resolved base directory does not exist or is not a directory. `discover_documents` runs it concurrently with `discover_document_stored` in an `anyio` task group, so the error cancels the store lookup and surfaces wrapped in an `ExceptionGroup`.

A category defined in configuration and populated through document ingestion need not have a docroot directory, so the existence check is the wrong place to fail.

## Goals / Non-Goals

**Goals:**
- A missing base directory means "no filesystem files" at the lowest level, so no caller and no task group ever sees it.
- Stored documents are always consulted.

**Non-Goals:**
- Changing validation errors for a relative base path or errors on an existing but unreadable directory.
- Creating category directories on `category_add`.
- Restructuring the task group or unwrapping exception groups generally.

## Decisions

1. **Fix in `discover_document_files`: return an empty `FileInfoList` when the directory is missing or not a directory.** Every caller, including the task group in `discover_documents` and `category_list_files`, is then correct without special cases. Alternatives: guard in the tool only (leaves content gathering and the task group exposed); add a `missing_dir_ok` flag (every caller would need to opt in, and the task-group path would still need it threaded through). Both rejected in favour of one rule at the source.

2. **Keep the absolute-path check before the existence check.** A relative base path is a programming error, not an absent directory, and keeps raising `ValueError`. Pattern validation remains after the availability check because patterns do not matter when no filesystem search can occur.

3. **Log the skip at debug level** for diagnostics without treating the cause of an absent path as an error. The system makes no distinction between a store-only category, an empty category whose directory was never created, or any other absent/non-directory category path.

4. **Leave `category_list_files` unchanged apart from tests.** The `source: files` path already calls `discover_document_files`, the default path calls `discover_documents`, and the `stored` path never touched the directory.

5. **Empty result, not `None`.** The store lookup already returns an empty list for a category with nothing in it; the return types stay `FileInfoList`.

## Risks / Trade-offs

- [An absent or non-directory category path yields an empty filesystem listing] → Debug log of the skipped path; `category_list` still shows the configured `dir`. This is the intended behaviour regardless of why the path is absent.
- [Callers that relied on the exception] → Audited:
  - `render/rendering.py` `discover_single_file` already raises its own `FileNotFoundError` when nothing is found, so template lookups still fail clearly.
  - `prompts/guide_prompt.py` already returns "Command not found" for an empty result.
  - `discovery/commands.py` filters an empty list.
  - `content/gathering.py` already handles an empty result.
  - `tools/tool_resource.py` skill discovery caught `OSError` to retain a cached result; with a missing skills directory it will now treat the result as empty rather than retaining the cache. Verify this during implementation and keep the previous behaviour if a test shows a regression.
- [Existing test asserts `FileNotFoundError`] → Update it to the new contract (`tests/unit/test_mcp_guide/discovery/test_files.py::test_directory_not_found`).
