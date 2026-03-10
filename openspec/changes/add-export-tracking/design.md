# Design: Export Tracking

## Context

The `export_content` tool (added in `add-knowledge-export`) allows agents to export rendered content to their filesystem for knowledge indexing. Agents may repeatedly export the same content, wasting tokens and context window when the underlying files haven't changed.

## Goals

- Track successful exports per project (expression, path, timestamp)
- Detect when exported content is still current (no file changes since export)
- Return early with "already available" message when content unchanged
- Minimal overhead: leverage existing file discovery with mtime filtering

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
  '["docs", null]':
    path: ".knowledge/docs.md"
    mtime: 1710072000.0
  '["docs", "*.md"]':
    path: ".knowledge/docs-md.md"
    mtime: 1710071000.0
```

**Rationale:**
- Tuple key `(expression, pattern)` captures uniqueness (pattern affects content)
- Pattern is None if not provided
- Simple dict lookup by tuple
- YAML serializes tuples as JSON arrays

**Alternatives considered:**
- Expression-only key → wrong, pattern affects content returned
- List of records → requires linear search, allows duplicates
- Separate tracking file → unnecessary complexity

### Staleness Detection: mtime Filtering

Pass `updated_since` timestamp to file discovery. Discovery filters files where `mtime <= updated_since` during traversal.

```python
# In discovery.py
if updated_since and file_stat.st_mtime <= updated_since:
    continue  # Skip unchanged file
```

**Rationale:**
- Generic parameter name: `updated_since` describes filtering behavior
- Simple: single comparison per file during existing traversal
- Efficient: no separate stat calls, no content hashing
- Sufficient: mtime changes indicate content changes

**Force flag:** Pass `updated_since=None` to bypass filtering

**Alternatives considered:**
- Content hashing → expensive, unnecessary precision
- Separate staleness check → duplicate traversal overhead
- Compare file count only → misses updates to existing files

### Early Return: "Already Available" Message

When all files filtered out (no changes detected):

```
Content already exported to .knowledge/docs.md (exported 2m ago, no changes detected)
```

For kiro-cli/q-dev agents, append: "and indexed in knowledge base"

**Rationale:** Informative, actionable, agent-specific context

### Force Flag: Override Staleness Check

`force=True` bypasses tracking lookup and staleness check, always exports.

**Rationale:** Allows manual refresh when needed (e.g., template changes, flag changes)

## Risks / Trade-offs

**Risk:** mtime-based staleness may miss changes if file touched without content change
**Mitigation:** `force` flag allows manual override; false positives (unnecessary export) are acceptable

**Risk:** Export tracking grows unbounded
**Mitigation:** Deferred to future change if needed; typical projects have <100 exports

**Trade-off:** Storing full expression + pattern vs hash
**Decision:** Store full expression/pattern for debuggability and potential query tool

## Migration Plan

- Non-breaking: existing `export_content` calls work unchanged
- New `exports` field in project config (optional, defaults to empty list)
- No data migration needed

## Open Questions

None
