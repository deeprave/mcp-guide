## Why

Stored document names can contain control characters and are later interpolated
into CRLF-delimited MIME `Content-Location` headers. This permits a client that
can ingest or rename a document to inject MIME part headers when MIME content
formatting is selected.

## What Changes

- Reject document names containing CR, LF, NUL, or any other Unicode control
  character at document ingestion, direct store upsert, and rename boundaries.
- Preserve existing stored rows but ensure MIME serialisation percent-encodes URI
  path segments, including reserved characters and controls, before building a
  `Content-Location` header.
- Apply the same safe location construction to single-document and multipart MIME
  output.
- Return a stable validation failure for unsafe new names without modifying an
  existing document row.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `document-store`: Prevent storage and rename of document names containing
  control characters.
- `content-formatting`: Encode MIME `Content-Location` URI path segments so
  stored names cannot create additional MIME headers.

## Impact

- Affected code: document event ingestion, SQLite add/update operations, stored
  document discovery, and MIME single/multipart formatting.
- Affected behaviour: invalid names are rejected at persistence boundaries;
  ordinary names retain their logical path while spaces, Unicode, reserved
  characters, and legacy controls have URI-safe MIME locations.
