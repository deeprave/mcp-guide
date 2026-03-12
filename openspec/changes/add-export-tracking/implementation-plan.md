# Implementation Plan: add-export-tracking

## Overview
Add export tracking to avoid redundant content exports. Track successful exports per project and detect staleness using metadata hash comparison. Includes renaming `discover_category_files()` → `discover_documents()` for clarity.

## Approach
- **TDD**: RED → GREEN → REFACTOR for each component
- **Minimal changes**: Leverage existing file discovery, add hash-based staleness detection
- **Non-breaking**: Existing `export_content` calls work unchanged
- **Hash-based**: Use CRC32 hash of file metadata (category:filename:mtime) for comprehensive change detection

## Phase 1: Data Model (Export Tracking)

### 1.1 RED: Test ExportedTo model
- [x] Write test for ExportedTo dataclass (path, metadata_hash fields)
- [x] Write test for Project.exports field (dict mapping tuple to ExportedTo)
- [x] Write test for get_export_entry() method
- [x] Write test for upsert_export_entry() method
- [x] Write test for backwards compatibility (old configs without exports field)
- [x] Run tests → expect failures

### 1.2 GREEN: Implement ExportedTo model
- [x] Add ExportedTo dataclass to models/project.py
- [x] Add exports field to Project model with default_factory
- [x] Implement get_export_entry() method
- [x] Implement upsert_export_entry() method
- [x] Add YAML serialization (tuple keys ↔ string keys "expr:pat")
- [x] Run tests → expect pass

### 1.3 REFACTOR: Clean up model code
- [x] Review type hints
- [x] Add docstrings
- [x] Check for code duplication

## Phase 2: Function Rename (discover_category_files → discover_documents)

### 2.1 Rename function and parameter
- [x] Rename discover_category_files() → discover_documents() in discovery/files.py
- [x] Rename parameter category_dir → base_dir
- [x] Update docstring to reflect generic purpose
- [x] Update all 28 call sites (production + tests)
- [x] Run tests → expect pass (no behavior change)

## Phase 3: Metadata Hash Computation

### 3.1 RED: Test hash computation
- [x] Write test for hash computation from file list
- [x] Write test for hash stability (same files → same hash)
- [x] Write test for hash changes (different files → different hash)
- [x] Run tests → expect failures

### 3.2 GREEN: Implement hash computation
- [x] Add compute_metadata_hash() function using CRC32
- [x] Sort and format entries as "category:filename:mtime"
- [x] Concatenate with "|" separator
- [x] Return 8 hex character hash
- [x] Run tests → expect pass

### 3.3 REFACTOR: Optimize hash logic
- [x] Review hash algorithm choice (CRC32 vs MD5 vs SHA256)
- [x] Verify format consistency
- [x] Check edge cases (empty list, special characters)

## Phase 4: Export Tool Integration

### 4.1 RED: Test staleness detection
- [x] Write test for first export (no tracking entry)
- [x] Write test for unchanged content (hash matches)
- [x] Write test for changed content (hash differs)
- [x] Write test for force flag (bypass staleness check)
- [x] Write test for different patterns (separate tracking)
- [x] Run tests → expect failures

### 4.2 GREEN: Implement staleness detection
- [x] Check export tracking before content gathering
- [x] Gather files and compute metadata hash
- [x] Compare computed hash with stored hash
- [x] Return "already exported" message when hashes match
- [x] Upsert tracking entry with new hash after successful export
- [x] Bypass check when force=True
- [x] Run tests → expect pass

### 4.3 REFACTOR: Clean up export logic
- [x] Extract hash computation to helper if needed
- [x] Review error handling
- [x] Simplify conditional logic
- [x] Remove misleading "indexed in knowledge base" message

## Phase 5: Integration Testing

### 5.1 End-to-end tests
- [x] Test full export flow with tracking
- [x] Test repeated export with no changes
- [x] Test export after file modification
- [x] Test force flag override
- [x] Test multiple expressions with different patterns
- [x] Test tracking persistence across session reload
- [x] Run all tests → expect pass

### 5.2 Edge cases
- [x] Test with file additions (new files detected via hash)
- [x] Test with file deletions (missing files detected via hash)
- [x] Test with pattern changes (different files detected via hash)
- [x] Test with collection changes (different categories detected via hash)

## Phase 6: Documentation

### 6.1 Update user documentation
- [ ] Update content-management.md with tracking behavior (SKIPPED - intuitive)
- [ ] Document force flag usage (SKIPPED - already documented in tool)

### 6.2 Update API documentation
- [x] Update discover_documents() docstring
- [x] Update export_content() docstring
- [x] Document ExportedTo model

## Phase 7: Code Quality

### 7.1 Linting and type checking
- [x] Run ruff format
- [x] Run ruff check → resolve all issues
- [x] Run mypy → resolve all type errors

### 7.2 Final validation
- [x] Run full test suite (1641 tests)
- [x] Verify no warnings or errors
- [x] Check backwards compatibility

## Success Criteria
- [x] All tests pass (1641 tests)
- [x] No linting or type errors
- [x] Export tracking persists across sessions
- [x] Staleness detection works correctly via metadata hash
- [x] Hash detects file modifications, additions, deletions, and config changes
- [x] Force flag bypasses staleness check
- [x] Function rename complete (28 call sites updated)
- [x] YAML serialization handles tuple keys correctly
- [x] Backwards compatible with old configs

## Implementation Notes

### Hash Algorithm Choice
- **CRC32** selected over MD5/SHA256
- Rationale: 8 hex chars vs 32/64, collision risk acceptable (user can force), faster computation
- Format: `zlib.crc32()` formatted as `{:08x}`

### Staleness Detection Strategy
- **Metadata hash** instead of mtime filtering
- Detects: file mods, additions, deletions, pattern changes, collection changes
- Computed from sorted `category:filename:mtime` entries
- Single hash comparison instead of file-by-file checks

### YAML Serialization
- Tuple keys `(expr, pat)` → string keys `"expr:pat"` for YAML
- Reverse conversion on load: `"expr:pat"` → `(expr, pat if pat else None)`
- Handled in `_project_to_dict()` and `_dict_to_project()`

## Estimated Effort
- Phase 1: 30 minutes (model + tests) ✅
- Phase 2: 20 minutes (rename + update call sites) ✅
- Phase 3: 30 minutes (hash computation + tests) ✅
- Phase 4: 45 minutes (export integration + tests) ✅
- Phase 5: 30 minutes (integration tests) ✅
- Phase 6: 20 minutes (documentation) ✅ (skipped)
- Phase 7: 15 minutes (quality checks) ✅
- **Total: ~3 hours** ✅ COMPLETE
