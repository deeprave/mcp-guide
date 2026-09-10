# file-discovery Specification

## Purpose
Define how project documents are discovered from configured filesystem
categories and the local document store, including pattern matching,
source identity, and deduplication behavior before content rendering.

## Requirements

### Requirement: Document Discovery Function

The system SHALL provide a `discover_documents()` function that discovers files from both the filesystem and the document store, merged into a unified result.

The function SHALL be composed of two sub-functions:
- `discover_document_files(base_dir, patterns)` — filesystem discovery (existing behaviour)
- `discover_document_stored(category, patterns)` — query document store by category, filtered by patterns

The merged function applies category and pattern filtering uniformly to both sources.

#### Scenario: Discover filesystem files
- **WHEN** `discover_document_files(base_dir, patterns)` is called
- **THEN** files matching patterns in the directory are returned with FileInfo metadata

#### Scenario: Discover stored documents
- **WHEN** `discover_document_stored(category, patterns)` is called
- **THEN** documents matching the category and patterns are returned from the store

#### Scenario: Merged discovery
- **WHEN** `discover_documents()` is called with both filesystem and store context
- **THEN** results from both sources are combined
- **AND** each result indicates its source (filesystem or store)

### Requirement: Source-Aware Document Deduplication

The system SHALL deduplicate discovered documents using source-aware identity
rather than display basename.

Filesystem documents SHALL be identified by their source path identity. Stored
documents SHALL be identified by `(category, name)`. Filesystem and stored
documents SHALL remain distinct sources, even when their display names match.

#### Scenario: Files with same basename from different directories
- **WHEN** filesystem discovery matches multiple files with the same basename in
  different directories
- **THEN** all matching files SHALL be included
- **AND** no file SHALL be silently skipped because another file has the same
  basename

#### Scenario: Template and non-template variants of same source path
- **WHEN** filesystem discovery matches template and non-template variants of
  the same source path
- **THEN** the variants SHALL be deduplicated using the full relative path with
  template extension stripped
- **AND** the preferred variant SHALL be returned according to discovery rules

#### Scenario: Stored document overlaps multiple collections
- **WHEN** the same stored document is discovered through overlapping
  collections or expressions
- **THEN** the document SHALL appear once for its `(category, name)` identity

#### Scenario: Filesystem and stored document with same display name
- **WHEN** a filesystem document and a stored document have the same display name
- **THEN** both documents SHALL be returned
- **AND** they SHALL remain distinguishable by source

### Requirement: Size-Aware Bounded Content Selection

Document discovery SHALL preserve byte-size metadata for both filesystem and
stored documents without loading a document body. Filesystem metadata SHALL use
the source file byte length; stored-document metadata SHALL represent the UTF-8
byte length of the stored body.

When discovery supports a content request, it SHALL stop selection at the
configured request-wide document-count limit across all expanded expressions and
both sources. It SHALL report that the request limit was exceeded rather than
silently returning a truncated document set.

#### Scenario: Stored document size is available before loading content
- **WHEN** discovery selects a stored document for a content request
- **THEN** the selected document includes its UTF-8 byte size before its body is read
- **AND** discovery does not load the body solely to determine that size

#### Scenario: Multiple expressions exceed the combined document limit
- **WHEN** a content request combines categories or collections whose total distinct documents exceed the configured limit
- **THEN** selection fails with the request document-count limit
- **AND** it does not treat each expression as having an independent limit

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
