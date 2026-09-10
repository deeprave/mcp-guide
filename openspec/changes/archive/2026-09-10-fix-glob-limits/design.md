## Context

See [proposal.md](proposal.md) for the motivation. Recursive matching currently
uses `os.walk()` to collect every matching path, sorts that complete list, and only
then lets the result cap stop candidate processing. The sort is what makes result
selection stable today, but it also leaves traversal and allocation unbounded in a
wide tree.

The existing contract has two ordering dimensions that must remain intact where a
directory fits within its bounded entry set: supplied patterns have precedence
during selection, while returned selected paths are sorted by path. A directory
that exceeds the per-directory entry budget is an explicit exception: its native
enumeration prefix is selected, sorted, and reported as truncated.

## Goals / Non-Goals

**Goals:**

- Bound discovery work before arbitrary candidate collection or sorting occurs.
- Preserve the current selected set and canonical returned order for searches
  whose relevant directories fit within the new budgets.
- Make exhausted guards observable warnings attached to bounded successful
  results, not silent data-dependent truncation.

**Non-Goals:**

- Changing glob syntax, pattern precedence, the 100-document result cap, depth
  limits, extension fallback, or symlink semantics.
- Providing per-project or runtime-configurable glob budgets in this change.
- Optimising stored-document discovery, which does not use filesystem traversal.

## Decisions

### Deterministic bounded traversal replaces whole-tree collection

Implement an incremental traversal iterator that reads entries for one directory
at a time, stops collecting after the per-directory budget, then sorts that bounded
set using a case-sensitive POSIX relative-path key. For directories within the
budget, traversal visits candidate paths in the order needed to produce the same
canonical set that the current complete-list sort would select. A wider directory
uses the native-enumeration prefix; this deliberate portability limitation is
recorded as truncation.
The iterator retains a resolved-directory set for cycle detection and preserves
existing validity/depth checks.

Non-recursive matching will use the same deterministic entry source rather than
delegating final ordering to host `glob` iteration. Recursive and non-recursive
forms therefore share an ordering contract.

Alternative considered: stop `os.walk()` after the first 100 matches. Rejected:
directory order differs across APFS, ext4, and other filesystems, so it changes
which documents are returned. Alternative considered: keep collecting and apply a
maximum candidate list size. Rejected: it can still stop before a lexically earlier
candidate has been discovered and silently changes results.

### Preserve selection precedence, then sort the selected result

The search will process patterns in their supplied order. For each pattern, it
consumes the canonical candidate stream, validates/de-duplicates candidates, and
adds them until the shared 100-document cap is full. It then returns the selected
set in canonical path order, matching the current public result ordering.

Once the cap is reached, later patterns cannot alter the selected set because their
selection precedence is lower. The iterator can therefore stop without traversing
them. For the active pattern, traversal only stops after its canonical stream has
established the selected prefix; it never substitutes discovery order for canonical
order.

Alternative considered: globally merge every pattern into one lexical stream.
Rejected because that would change the established priority of earlier supplied
patterns when the cap is reached.

### Return bounded results with observable truncation

Add fixed discovery constants: 128 pattern expressions, 4,096 entries per
directory, 65,536 entries per search, and a two-second accumulated enumeration
budget. Count all entry inspection, including non-recursive patterns and extension
fallback. Measure only time spent enumerating directory/glob entries; exclude
sorting, validation, de-duplication, rendering, and other downstream processing.

If a guard prevents completing the search, stop further enumeration, retain the
bounded matches already selected, and record the reached guard. The discovery
boundary logs a warning; public content results aggregate the reached guards in a
successful `message` so callers know the result may be truncated. The same applies
when the existing depth limit prunes a directory.

The bounded-directory prefix is intentionally accepted because document trees are
server-controlled and this guard is not expected to be reached in normal use. It
avoids unbounded work while making the exceptional loss of determinism visible.

## Risks / Trade-offs

- [A legitimate wide directory is truncated] → Use deliberately generous finite
  defaults, log the reached guard, and include it in the successful result message.
- [Directory-local sorting changes traversal cost] → Bound entries before sorting;
  a bounded sort is necessary to preserve canonical output across host filesystems.
- [A two-second enumeration budget is sensitive on slow storage] → Accumulate only
  enumeration time, test with an injected clock, and warn while returning the
  bounded result rather than allowing unbounded server work.
- [Complex glob forms diverge from current matching] → Keep existing match syntax
  tests and add compatibility cases for nested, wildcard, extensionless, symlink,
  and overlapping-pattern behaviour.

## Migration Plan

1. Introduce limit constants, truncation diagnostics, and incremental
   directory-entry traversal behind focused unit tests.
2. Replace recursive and non-recursive candidate enumeration while retaining the
   existing validation, de-duplication, fallback, and final ordering behaviours.
3. Propagate accumulated truncation guards through document discovery and content
   tools as warning messages on successful results.
4. Add wide-tree, reversed-enumeration, pattern-precedence, and deadline tests;
   run discovery and integration suites before release.

No persisted data changes or migration are required. Rolling back restores the
previous traversal implementation.
