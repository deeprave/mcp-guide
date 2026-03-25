# Change: Add document_update tool

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

The document store currently supports add (upsert) and remove, but lacks granular mutation operations. To rename, move, or update metadata on a stored document, the only option is to re-add the entire document with new parameters. This is wasteful for metadata-only changes and error-prone for rename/move since the caller must also remove the old entry.

Additionally, `category_list_files` does not surface descriptions for stored documents — it only extracts descriptions from filesystem file frontmatter, skipping store-sourced entries entirely. Stored documents already have description available in their metadata dict (populated from frontmatter during ingestion), but it's not consulted.

## What Changes

### 1. document_update tool

New `document_update` tool for in-place mutation of stored documents.

Required parameters:
- `category` — current category (must exist, document must be found)
- `name` — current document name

Optional parameters:
- `new_name` — rename the document
- `new_category` — move to a different category (must exist)
- `metadata_add` — dict of entries to merge into existing metadata
- `metadata_replace` — dict that replaces the entire metadata
- `metadata_clear` — list of metadata keys to remove

At least one optional parameter must be provided.

Metadata operations are mutually exclusive — specifying more than one of `metadata_add`, `metadata_replace`, or `metadata_clear` is a validation error.

Collision handling: if the target (new_category, new_name) combination already exists, return an error. The caller must remove the conflicting document first.

Fields not exposed for mutation: `source`, `source_type`, `content`. These are set during ingestion and have no use case for post-hoc changes.

### 2. document_show command

New `_commands/document/show` template that displays full detail for an existing stored document including all metadata fields, source, timestamps, and content size.

### 3. document_update command

New `_commands/document/update` template that handles all mutation combinations (rename, move, metadata operations) with appropriate output for each.

### 2. Store description in category_list_files

Fix `category_list_files` to read description from `record.metadata["description"]` for store-sourced documents, matching the existing behaviour for filesystem files.

### 3. Command templates

Add `_commands/document/show.mustache` for displaying full document detail and `_commands/document/update.mustache` for mutation result output.

## Technical Approach

### Store layer

Add `_update_document()` to `document_store.py`:
- Lookup existing record by (category, name), fail if not found
- If new_name or new_category specified, check target doesn't already exist
- Apply metadata operations in order: clear → replace → add
- Single UPDATE statement for all changed fields
- Return updated DocumentRecord

### Tool layer

Add `tool_document_update.py` with `DocumentUpdateArgs` and `document_update` tool following existing tool patterns (`@toolfunc`, `internal_` function, `tool_result`).

### Discovery fix

In `category_list_files`, when `file.source == "store"`, retrieve description from the document record's metadata dict instead of skipping it.

## Success Criteria

- Documents can be renamed, moved between categories, and have metadata updated without re-ingestion
- Collisions on rename/move are detected and reported as errors
- `category_list_files` shows descriptions for stored documents
- Metadata operations (add, replace, clear) work independently and in combination
