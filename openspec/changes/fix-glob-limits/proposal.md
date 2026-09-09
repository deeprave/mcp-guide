## Why

Recursive globbing builds and sorts every candidate before applying its
100-document cap. A wide directory tree can therefore consume unbounded
enumeration, memory, and sort work even though the caller receives only a small
result set.

## What Changes

- Replace recursive candidate collection with bounded, incremental traversal
  that sorts a limited set of entries from one directory at a time.
- Preserve canonical path-sorted result semantics for directories within the
  entry budget. When a directory exceeds that budget, select and sort its
  native-enumeration prefix, and report the resulting portability limitation.
- Introduce finite limits for patterns, directory entries, total traversal work,
  and elapsed traversal time.
- Log and report traversal-limit truncation without failing an otherwise useful
  result.
- Retain the existing depth, symlink-cycle, validity, de-duplication, extension
  fallback, and 100-document result limits.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `file-discovery`: Make recursive filesystem glob discovery incrementally
  resource-bounded while preserving canonical selection except for documented
  wide-directory truncation.

## Impact

- Affected code: glob traversal and candidate processing in
  `src/mcp_guide/discovery/patterns.py`, discovery constants, and filesystem
  discovery tests.
- Affected behaviour: over-budget recursive searches return their bounded result
  with a warning naming every reached guard. Successful searches remain canonically
  ordered except where a directory's native-enumeration prefix exceeds the
  per-directory budget.
