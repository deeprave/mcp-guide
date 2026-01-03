# Change: Fix File Deduplication Bug

## Why

Currently, when processing collections that contain files with the same basename from different categories, only the first file is included. This causes important content to be silently skipped.

**Example:**
- Collection `code-review` contains categories `guidelines` and `review`
- `guidelines` category has `guide/general.md`
- `review` category has `review/general.md`
- Only `guide/general.md` is processed, `review/general.md` is skipped

The deduplication logic uses only the basename (`general.md`) instead of the full relative path (`guide/general.md` vs `review/general.md`).

## What Changes

- **Affected specs**: content-processing
- **Affected code**: File discovery and deduplication logic in content processing system
- Change deduplication key from basename to full relative path
- Ensure files with same name from different categories are both included

## Impact

- Fixes silent content skipping bug
- Ensures all intended files are processed in collections
- Maintains proper separation between categories
- No breaking changes to existing functionality
