## ADDED Requirements

### Requirement: Canonical Filesystem Glob Selection

For a filesystem glob search whose relevant directories do not exceed the
per-directory entry budget, the system SHALL select candidates in a
filesystem-independent canonical order: ascending, case-sensitive POSIX relative
path order. It SHALL apply this order before the existing document result limit
selects a subset, so equivalent directory trees return the same paths on every
supported filesystem.

When multiple patterns are supplied, the system SHALL retain their supplied
precedence: it SHALL process each pattern's unique valid candidates in canonical
path order, stop selection at the existing shared document result limit, and return
the selected set sorted in canonical path order. Existing validity filtering,
extension fallback, de-duplication, depth limits, and symlink-cycle handling SHALL
remain unchanged.

#### Scenario: Different bounded directory enumeration orders select the same results
- **WHEN** equivalent directory trees are enumerated in different native filesystem orders
- **AND** the matching candidates exceed the document result limit
- **THEN** each successful search selects the same canonical paths
- **AND** each returned list is ordered by canonical relative path

#### Scenario: Earlier supplied pattern retains selection precedence
- **WHEN** overlapping supplied patterns together match more documents than the shared result limit
- **THEN** candidates selected for an earlier pattern retain precedence over later patterns
- **AND** candidates within each pattern are selected by canonical relative path rather than native enumeration order

### Requirement: Bounded Glob Traversal Work

The system SHALL apply finite glob traversal limits of 128 pattern expressions,
4,096 entries read from one directory, 65,536 entries read by one search, and two
seconds of accumulated monotonic directory/glob-entry enumeration time. These
limits SHALL include recursive walking, non-recursive matching, and extension
fallback. Sorting, validation, de-duplication, rendering, and other downstream
processing SHALL NOT consume the enumeration-time budget.

The system SHALL stop traversal as soon as the existing document result limit has
been selected when doing so cannot change the selected set. It SHALL NOT build or
sort an unbounded complete candidate list before applying that result limit.

#### Scenario: Wide directory exceeds the per-directory entry limit
- **WHEN** a glob search needs to inspect more than 4,096 entries in one directory
- **THEN** the search keeps and canonically sorts only the first 4,096 entries
  supplied by native directory enumeration
- **AND** the search returns its bounded result with a warning that the
  directory-entry limit truncated it
- **AND** the selected result is documented as potentially platform-dependent

#### Scenario: Search exceeds aggregate entry or time limit
- **WHEN** recursive traversal exceeds 65,536 inspected entries or two seconds of monotonic elapsed time
- **THEN** the search stops further enumeration and returns accumulated selected
  results
- **AND** the warning identifies whether the entry or enumeration-time budget was exhausted

#### Scenario: Result limit permits early completion without reordering
- **WHEN** canonical traversal has selected the maximum number of valid unique documents
- **AND** no later traversal work can alter the selected set under supplied-pattern precedence
- **THEN** the search stops without enumerating unrelated remaining directories
- **AND** it returns the same canonically ordered result set as a complete traversal

### Requirement: Observable Glob Traversal Truncation

The system SHALL log pattern-count, directory-entry, aggregate-entry,
enumeration-time, and depth-limit exhaustion. It SHALL return any bounded selected
results as a successful response and attach an aggregated message naming every
reached guard. It SHALL NOT silently skip candidates or report the bounded result
as a failure.

#### Scenario: Too many patterns are supplied
- **WHEN** a filesystem glob search receives more than 128 pattern expressions
- **THEN** it processes at most 128 expressions and returns a successful result
  with a pattern-count truncation warning
