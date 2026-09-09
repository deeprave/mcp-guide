## 1. Bounded deterministic traversal

- [ ] 1.1 Add fixed pattern, per-directory-entry, aggregate-entry, and monotonic-time glob limits plus a dedicated limit exception, and verify unit tests reject each exhausted budget with its identified reason.
- [ ] 1.2 Replace recursive whole-tree candidate collection with a bounded canonical directory-entry iterator that preserves depth, validity, and symlink-cycle safeguards, and verify no traversal path builds an unbounded candidate list.
- [ ] 1.3 Route non-recursive matching through the same canonical ordering mechanism, and verify existing wildcard, nested-path, extensionless fallback, and symlink discovery tests still pass.

## 2. Result selection and failure propagation

- [ ] 2.1 Apply the existing shared document cap while consuming canonical candidates in supplied-pattern precedence, then canonically sort the selected result, and verify reversed native enumeration selects the same paths as normal enumeration.
- [ ] 2.2 Stop after the selected canonical prefix when later traversal cannot affect it, and verify a wide tree beyond the selected prefix is not enumerated.
- [ ] 2.3 Propagate traversal guard exhaustion through filesystem discovery and content callers as `glob_limit_exceeded`, and verify callers receive no partial or silently truncated successful result.

## 3. Regression coverage and validation

- [ ] 3.1 Add focused tests for per-directory, aggregate-entry, pattern-count, and injected monotonic-deadline limits, and verify each keeps successful output deterministic when below its budget.
- [ ] 3.2 Add compatibility tests for overlapping-pattern precedence and canonical output across simulated APFS/ext4-style enumeration orders, and verify the prior selected result set is preserved for successful searches.
- [ ] 3.3 Run `uv run pytest tests/unit/test_mcp_guide/discovery/test_patterns.py` and relevant content-discovery integration tests in the foreground, and verify they complete without regression failures.
- [ ] 3.4 Validate the completed OpenSpec change with `openspec validate fix-glob-limits --type change --strict` and verify no validation errors remain.
