## 1. Record the baseline
- [x] 1.1 Record the current suite baseline in the change artifacts
- [x] 1.2 Confirm the current full-suite runtime and passing test count
- [x] 1.3 Confirm the current overall coverage percentage and statement counts

## 2. Audit the current suite
- [x] 2.1 Review `tests/unit/test_mcp_guide/discovery/test_files.py` for trivial field and dataclass tests
- [x] 2.2 Review `tests/unit/test_mcp_core/test_validation.py` for framework-oriented or repetitive validator cases
- [x] 2.3 Review `tests/unit/test_mcp_guide/tools/test_tool_collection.py` for duplicate tool-behavior cases
- [x] 2.4 Review `tests/unit/test_mcp_guide/tools/test_tool_category.py` for duplicate tool-behavior cases
- [x] 2.5 Review `tests/unit/test_mcp_guide/tools/test_tool_project.py` for duplicate tool-behavior cases
- [x] 2.6 Review `tests/test_template_functions.py` for framework-behavior or overly granular helper tests
- [x] 2.7 Review `tests/test_template_context_cache.py` for repeated context-shape assertions
- [x] 2.8 Review other small or repetitive files discovered during the audit

## 3. Remove or consolidate low-signal tests
- [x] 3.1 Remove tests that only assert trivial field storage or feature presence
- [x] 3.2 Remove tests that only restate Python, pytest, asyncio, or library behavior
- [x] 3.3 Consolidate duplicate cases using `pytest.mark.parametrize`
- [x] 3.4 Merge tiny files into related modules where that improves clarity
- [x] 3.5 Keep a brief rationale in the change notes for any broad removal batch

## 4. Protect high-value coverage
- [x] 4.1 Preserve meaningful integration coverage
- [x] 4.2 Preserve security, path-handling, and workflow-state coverage
- [x] 4.3 Preserve regression tests for recently fixed bugs
- [x] 4.4 Add or keep a stronger test where a broad set of weak tests is being replaced

## 5. Validate each reduction batch
- [x] 5.1 Run focused tests for each touched area
- [x] 5.2 Run the full suite after major removal or consolidation batches
- [x] 5.3 Re-check coverage after major removal or consolidation batches
- [x] 5.4 Confirm that the final suite remains green under the standard quality checks

## 6. Record the outcome
- [x] 6.1 Record final before/after test counts
- [x] 6.2 Record final before/after runtime
- [x] 6.3 Record final before/after coverage summary
- [x] 6.4 Note any follow-up areas intentionally deferred

## First-pass audit outcome

- Removed trivial schema/default/presence tests from:
  - `tests/unit/test_mcp_guide/discovery/test_files.py`
  - `tests/unit/test_mcp_guide/tools/test_tool_category.py`
  - `tests/unit/test_mcp_guide/tools/test_tool_project.py`
- Consolidated repeated behavior tests with parameterization in:
  - `tests/unit/test_mcp_core/test_validation.py`
  - `tests/unit/test_mcp_guide/tools/test_tool_collection.py`
  - `tests/unit/test_mcp_guide/test_uri_parser.py`
  - `tests/test_template_context_cache.py`
  - `tests/test_template_functions.py`
- No test files were merged in this pass because the audited candidates were clearer as in-place reductions than as file moves.
- No stronger replacement tests were needed in this pass because the removed cases were either trivial storage/presence assertions or direct duplicates of existing behavioral coverage.

## Follow-up audit outcome

- Further consolidated setup-heavy category tool tests in:
  - `tests/unit/test_mcp_guide/tools/test_tool_category.py`
- Further reduced schema/default noise in:
  - `tests/unit/test_mcp_guide/tools/test_tool_project.py`
- The follow-up pass reduced total collected tests further, but did not produce a stable runtime improvement across early full-suite runs.

## Runtime optimization outcome

- Re-profiled the suite with pytest duration reporting
- Replaced the slow throwaway-virtualenv console-script test in:
  - `tests/unit/scripts/test_mcp_guide_install.py`
  - with a cheaper packaging-contract test that verifies the `pyproject.toml` script mapping and invokes the mapped Click command directly
- Added configurable lock retry timing in:
  - `src/mcp_guide/file_lock.py`
  - while keeping the production default unchanged
- Reduced lock-related test waits in:
  - `tests/test_file_lock.py`
  - `tests/integration/test_config_session.py`
- Replaced repeated `switch_project()` setup in shared test helpers and hot unit/integration fixtures with direct bound-session setup where the tests only need a project bound, not switch notifications or watcher startup
- The runtime-focused pass produced the material duration improvement that simple test-count reduction did not.

## Before / After

- Full suite:
  - before: `1754 passed in 74.27s`
  - after: `1758 passed in 34.19s`
- Coverage:
  - before: `84%` (`9028` statements, `1463` missed)
  - after: `84%` (`9032` statements, `1488` missed)
- Collected tests:
  - before: `1754`
  - after: `1758`
- Test files:
  - unchanged at `159` total
  - `95` unit-test files
  - `24` integration-test files

## Deferred follow-up

- If runtime reduction remains a priority, target the current slowest tests first:
  - `tests/integration/test_tool_registration.py::test_mcp_client_can_initialize_and_list_tools`
- At the current best full-suite run, every other test was below the `0.2s` duration-reporting threshold.
- Any further work should be duration-driven rather than another broad low-signal pruning pass
