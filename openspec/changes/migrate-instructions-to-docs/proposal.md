# Proposal

## Why

`INSTRUCTIONS.md` duplicates durable project guidance in a repository file even though Guide can now persist and serve instruction documents from its document store. Moving the useful project-level guidance into the store will make it available through the normal category workflow while removing obsolete, tool-specific direction.

## What Changes

- Curate a single stored `agent/instruction` document from the enduring architectural and testing guidance in `INSTRUCTIONS.md`.
- Retain guidance on async-first implementation, client/server filesystem boundaries, use of established infrastructure, public APIs, template discovery, and pytest fixtures.
- Omit personal-error framing, duplicated summaries, and agent-tool or stylistic prescriptions that are not durable project guidance.
- Delete the superseded root `INSTRUCTIONS.md` after the stored document is confirmed available through the `guide` category.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

This is a documentation and stored-content migration. It does not change the document-store or Guide-serving behaviour, so this change sets `skip_specs: true`.

## Impact

- Removes `INSTRUCTIONS.md` from the repository root.
- Adds one curated instruction document to the existing Guide document store under the `guide` category.
- Uses the existing `send_file_content` ingestion workflow and existing category retrieval behaviour; no code, API, or dependency changes are required.
