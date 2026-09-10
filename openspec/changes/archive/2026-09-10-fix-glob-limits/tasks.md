## 1. Bounded deterministic traversal

- [x] 1.1 Add fixed pattern, per-directory-entry, aggregate-entry, and accumulated enumeration-time glob limits plus truncation diagnostics, and verify focused unit tests identify each reached guard.
- [x] 1.2 Replace recursive whole-tree candidate collection with an incremental bounded directory-entry iterator that preserves depth, validity, and symlink-cycle safeguards, and verify no traversal path builds an unbounded candidate list.
- [x] 1.3 Route non-recursive matching through the same canonical ordering mechanism, and verify existing wildcard, nested-path, extensionless fallback, and symlink discovery tests still pass.

## 2. Result selection and failure propagation

- [x] 2.1 Apply the existing shared document cap while consuming canonical candidates in supplied-pattern precedence, then canonically sort the selected result for directories within budget; verify a wide directory reports its native-prefix truncation.
- [x] 2.2 Stop after the selected canonical prefix when later traversal cannot affect it, and verify a wide tree beyond the selected prefix is not enumerated.
- [x] 2.3 Propagate accumulated truncation guards through filesystem discovery and content callers as logged successful-result messages, and verify callers receive bounded results with no silent truncation.

## 3. Regression coverage and validation

- [x] 3.1 Add focused tests for per-directory, aggregate-entry, pattern-count, depth, and injected accumulated-enumeration-time limits, and verify each logs and reports a successful bounded result.
- [x] 3.2 Add compatibility tests for overlapping-pattern precedence and canonical output across simulated APFS/ext4-style enumeration orders when directories fit the entry budget, plus the documented wide-directory exception.
- [x] 3.3 Run `uv run pytest tests/unit/test_mcp_guide/discovery/test_patterns.py` and relevant content-discovery integration tests in the foreground, and verify they complete without regression failures.
- [x] 3.4 Validate the completed OpenSpec change with `openspec validate fix-glob-limits --type change --strict` and verify no validation errors remain.
