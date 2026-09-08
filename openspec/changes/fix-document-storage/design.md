## Context

See [proposal.md](proposal.md) for the motivation. Document ingestion derives a
name from an event or client path, SQLite accepts that name on add and rename, and
stored discovery later reconstructs it as a `Path`. The optional MIME formatter
interpolates the resulting location directly into CRLF-delimited part headers.

The store may contain rows written before this fix or altered outside the normal
API. Input validation alone therefore cannot make MIME rendering safe.

## Goals / Non-Goals

**Goals:**

- Block control characters before they enter new or renamed stored document names.
- Make MIME header construction safe for both new and legacy stored names.
- Retain nested document paths, existing name semantics, content types, and
  logical MIME location structure.

**Non-Goals:**

- Changing outer HTTP response headers or transport encoding.
- Renaming, deleting, or migrating existing rows automatically.
- Restricting ordinary Unicode, spaces, or URI-reserved characters in document
  names beyond their safe URI representation.

## Decisions

### Validate control characters in the store, not only the event task

Introduce one shared document-name validation helper that rejects Unicode control
code points. Invoke it in the SQLite add/upsert and update/rename paths before any
transactional mutation. The event task will validate before parsing or storing to
give callers an immediate clear failure, while the store remains the authoritative
boundary for direct callers and future ingestion paths.

This is chosen over only validating names in `DocumentTask` because the public
store API already supports direct upserts and rename operations. It is chosen over
an ASCII-only allow-list because nested paths and Unicode names are supported
document identifiers and are not themselves unsafe in MIME when encoded.

### Build MIME locations from encoded segments

After existing template-extension stripping and MIME content-type extension
selection, split the relative document path into its POSIX segments and percent-
encode each segment from UTF-8 bytes. Join the encoded segments with literal `/`
and construct the `guide://` URI once through a shared formatter helper. Use that
helper in both single and multipart formatting paths.

Segment encoding is chosen over quoting the full path so hierarchy remains visible
and separators cannot be encoded accidentally. It also encodes `%`, spaces,
non-ASCII, and controls consistently. Reusing one helper prevents the single and
multipart paths drifting into different header-safety rules.

Alternative considered: strip CR/LF at formatting time. Rejected because silent
normalisation changes document identity and does not cover other control or
reserved characters. Alternative considered: trust the store after validation.
Rejected because legacy or externally modified SQLite rows remain possible.

### Preserve existing rows and validate their serialisation

No schema migration or bulk cleanup is needed. Existing invalid names remain
readable as data but their MIME representation is percent-encoded, preventing raw
header control bytes. New attempts to insert or rename such names fail without
modifying an existing row.

## Risks / Trade-offs

- [Clients compare literal MIME locations] → URI encoding changes representation
  only where names need it; safe ASCII paths keep their existing location text.
- [A legacy row uses controls intentionally] → It remains stored but is represented
  safely in MIME; operators can rename it through a safe name if needed.
- [Different code paths build locations] → Centralise construction and cover
  single/multipart outputs with parser-based tests that assert no MIME defects or
  injected fields.
- [Unicode classification edge cases] → Use the standard Unicode control category
  rather than a short list of ASCII characters, with C0/C1 regression cases.

## Migration Plan

1. Add the shared control-character validator to store add/upsert and rename
   paths, and return the established validation failure through document events.
2. Add one encoded content-location helper and route both MIME formatting paths
   through it.
3. Add store, ingestion, and MIME regression tests for CRLF/NUL/C1 input, legacy
   rows, reserved characters, nested paths, and valid Unicode names.

No data migration is required. Rollback restores prior acceptance and rendering,
but affected deployments should retain the hardened version to avoid MIME header
injection.
