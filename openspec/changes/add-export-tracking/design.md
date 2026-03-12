# Design: Export Tracking

## Context

The `export_content` tool (added in `add-knowledge-export`) allows agents to export rendered content to their filesystem for knowledge indexing. Agents may repeatedly export the same content, wasting tokens and context window when the underlying files haven't changed.

## Goals

- Track successful exports per project (expression, path, metadata hash)
- Detect when exported content is unchanged (comprehensive change detection)
- Return early with "already exported" message when content unchanged
- Minimal overhead: single hash comparison instead of file-by-file checks

## Non-Goals

- Track export failures or errors
- Analytics or usage statistics
- Cache invalidation or cleanup
- Workflow integration
- Validate exported files still exist on disk

## Decisions

### Storage: Project Configuration

Export tracking stored in project config as dict mapping (expression, pattern) tuple to export metadata:

```yaml
exports:
  docs::
    path: ".knowledge/docs.md"
    metadata_hash: "a3f5c8d1"
  docs:*.md:
    path: ".knowledge/docs-md.md"
    metadata_hash: "b2e4f9a7"
```

**Rationale:**
- Tuple key `(expression, pattern)` captures uniqueness (pattern affects content)
- Pattern is None if not provided (serialized as empty string after colon)
- Simple dict lookup by tuple
- YAML serialization converts tuple keys to strings "expr:pat" for compatibility

**Alternatives considered:**
- Expression-only key → wrong, pattern affects content returned
- List of records → requires linear search, allows duplicates
- Separate tracking file → unnecessary complexity

### Staleness Detection: Metadata Hash

Compute CRC32 hash of file metadata (category:filename:mtime) for all gathered files. Compare with stored hash.

```python
def compute_metadata_hash(files: list[FileInfo]) -> str:
    entries = sorted(
        f"{f.category.name}:{f.path.name}:{f.mtime.timestamp()}"
        for f in files
    )
    data = "|".join(entries).encode()
    return f"{zlib.crc32(data):08x}"  # 8 hex chars
```

**Rationale:**
- **Comprehensive detection:** Catches file modifications, additions, deletions, pattern changes, collection changes
- **Efficient:** Single hash comparison vs file-by-file checks
- **Compact:** 8 hex characters (CRC32) vs 32 (MD5) or 64 (SHA256)
- **Fast:** CRC32 is faster than cryptographic hashes
- **Sufficient:** Collision risk (~1 in 4B) acceptable, user can force override

**What it detects:**
- ✅ File modified (mtime changes)
- ✅ File added (new entry in hash input)
- ✅ File deleted (missing entry in hash input)
- ✅ Pattern changed (different files match)
- ✅ Collection membership changed (different categories)
- ✅ Category configuration changed (affects file discovery)
- ✅ Old file copied (new filename, even with old mtime)

**Force flag:** Bypasses hash comparison entirely

**Alternatives considered:**
- **mtime filtering only** → misses additions/deletions/config changes
- **File list tracking** → larger storage, more complex comparison
- **Config hash + mtime** → doesn't catch file additions/deletions
- **Content hashing** → expensive, unnecessary precision
- **MD5/SHA256** → longer hashes (32/64 chars), slower, overkill for this use case

### Early Return: "Already Exported" Message

When computed hash matches stored hash:

```
Content for 'docs' already exported to .knowledge/docs.md. Use force=True to overwrite or if file is missing.
```

**Rationale:**
- Informative: tells user where content was exported
- Actionable: explains how to override
- Honest: doesn't claim knowledge about indexing status (we only track exports)

**Removed:** "indexed in knowledge base" claim - we don't track indexing, only exports

### Force Flag: Override Staleness Check

`force=True` bypasses tracking lookup and hash comparison, always exports.

**Rationale:** Allows manual refresh when needed (e.g., template changes, flag changes, hash collision)

## Risks / Trade-offs

**Risk:** CRC32 collision causes false positive (skip export when content actually changed)
**Mitigation:**
- Collision probability ~1 in 4 billion
- User can use `force=True` to override
- False positive is annoying but not catastrophic

**Risk:** Export tracking grows unbounded
**Mitigation:** Deferred to future change if needed; typical projects have <100 exports

**Trade-off:** CRC32 vs cryptographic hash
**Decision:** CRC32 sufficient - 8 chars vs 32/64, faster, collision risk acceptable

**Trade-off:** Hash before or after rendering
**Decision:** Hash after gathering but before rendering - still wastes gathering work when stale, but keeps implementation simple. Future optimization could hash before rendering.

## Implementation Notes

### YAML Serialization

Tuple keys must be converted to strings for YAML compatibility:
- Serialize: `(expr, pat)` → `"expr:pat"` (empty string if pat is None)
- Deserialize: `"expr:pat"` → `(expr, pat if pat else None)`

Handled in `_project_to_dict()` and `_dict_to_project()` in session.py.

### Hash Algorithm

CRC32 chosen over MD5/SHA256:
- **Size:** 8 hex chars vs 32/64
- **Speed:** Faster than cryptographic hashes
- **Collision risk:** Acceptable for this use case
- **Stdlib:** `zlib.crc32()` available in Python stdlib

## Migration Plan

- Non-breaking: existing `export_content` calls work unchanged
- New `exports` field in project config (optional, defaults to empty list)
- No data migration needed

## Open Questions

None
