# Fix TOCTOU race in document upsert mtime check

## Problem

`document_task.py` performs a check-then-act pattern: it calls `get_document()` to read the existing mtime, compares it, then calls `add_document()` separately. This introduces a TOCTOU (time-of-check-to-time-of-use) race window where another write could occur between the read and the upsert.

## Current flow

```
existing = await get_document(category, name)     # READ
if existing.mtime >= mtime: return skip            # CHECK
await add_document(...)                            # ACT (separate transaction)
```

## Proposed fix

Move the mtime staleness check into the store layer's `_add_document()` as a conditional upsert within a single transaction. The store should:

1. Accept an optional `mtime` parameter
2. When `mtime` is provided and `force` is not set, compare against the existing row's mtime within the same transaction
3. Skip the write if the document is unchanged or newer, returning a result indicating the skip reason
4. Remove the `get_document()` call from `document_task.py`

This eliminates the race window and removes the extra query.

## Files affected

- `src/mcp_guide/store/document_store.py` — conditional upsert logic in `_add_document()`
- `src/mcp_guide/tasks/document_task.py` — remove `get_document()` check, pass mtime/force to store
