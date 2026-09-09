## Why

Recursive globbing builds and sorts every candidate before applying its
100-document cap. A wide directory tree can therefore consume unbounded
enumeration, memory, and sort work even though the caller receives only a small
result set.

## What Changes

- Replace recursive candidate collection with bounded, deterministic traversal
  that emits candidates in the same canonical path order used for result
  selection.
- Preserve the existing path-sorted result semantics across filesystem types;
  traversal shall not select a platform-dependent prefix based on directory
  enumeration order.
- Introduce finite limits for patterns, directory entries, total traversal work,
  and elapsed traversal time.
- Return an explicit glob-limit failure when a traversal cannot finish within a
  resource limit, rather than returning silently truncated or reordered results.
- Retain the existing depth, symlink-cycle, validity, de-duplication, extension
  fallback, and 100-document result limits.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `file-discovery`: Make recursive filesystem glob discovery deterministic and
  resource-bounded without changing the selected result set for successful
  searches.

## Impact

- Affected code: glob traversal and candidate processing in
  `src/mcp_guide/discovery/patterns.py`, discovery constants, and filesystem
  discovery tests.
- Affected behaviour: over-budget recursive searches fail deterministically with
  safe limit guidance; successful searches remain ordered by canonical relative
  path on every supported filesystem.
