# Tasks

## 1. Tests first

- [ ] 1.1 Replace `test_directory_not_found` with tests asserting `discover_document_files` returns an empty result for a missing directory and for a path that is a file; verify they fail against the current code
- [ ] 1.2 Add `discover_documents` tests for a store-only category (stored documents returned) and for no directory plus no stored documents (empty result); verify they fail against the current code
- [ ] 1.3 Add `internal_category_list_files` tests for a category with no docroot directory under default, `files` and `stored` sources; verify the default and `files` cases fail against the current code

## 2. Fix file discovery

- [ ] 2.1 Make `discover_document_files` return an empty `FileInfoList` (with a debug log) when the base directory is missing or not a directory, keeping the absolute-path `ValueError`, and verify the 1.1 to 1.3 tests pass
- [ ] 2.2 Run the existing discovery, content gathering, command, prompt, rendering and skill-discovery tests in the foreground and verify they pass; if the skill-discovery cache-retention test regresses, restore the previous behaviour for a missing skills directory and verify the test passes

## 3. Documentation and verification

- [ ] 3.1 Update documentation (`docs/`) to state that a category needs no docroot directory when its documents are ingested, and verify no stale statement remains by searching for the old wording
- [ ] 3.2 Run the full pytest suite and the project's lint and type checks in the foreground and verify they pass
- [ ] 3.3 Re-run `category_list_files` against the `openspec` category through the running server (after restarting it with the fix) and verify the default source returns `workspace-architecture.md`

## Workflow follow-up

- Archive the change after review requirements are satisfied.
