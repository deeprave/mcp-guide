# Design

## Context

See `proposal.md` for motivation. `INSTRUCTIONS.md` is a root-level, agent-facing source of project guidance. The document store now accepts client-provided documents and serves them through configured categories, so a separate repository copy is no longer needed.

## Goals / Non-Goals

**Goals:**

- Preserve concise, durable guidance that affects implementation decisions in this repository.
- Make that guidance available as an `agent/instruction` document in the existing `guide` category.
- Remove the migrated repository file once the stored document is available.

**Non-Goals:**

- Change document ingestion, retrieval, or category behaviour.
- Preserve agent-runtime rules, repeated summaries, or detailed stylistic preferences that do not form durable project guidance.
- Create a versioned replacement file for `INSTRUCTIONS.md`.

## Decisions

### Store one curated document in the `guide` category

The implementation will upload one document named `mcp-development.md` with `agent/instruction` metadata. Its source will identify the removed `INSTRUCTIONS.md` file. A single document keeps the material discoverable through the established guide category without splitting tightly related architectural constraints.

The retained content will cover async-first code and I/O, the client/server filesystem boundary, reuse of existing infrastructure, foreign-class public APIs, template discovery and rendering, and pytest fixture preferences. The migration will omit repeated warnings and workflow/tool commands, including the text-transformation prohibition, because those belong to the active agent environment rather than the project knowledge base.

### Upload before removal

The document will be ingested and retrieved through `category_list_files` before deleting the root file. This gives a direct availability check and avoids a gap in project guidance.

## Risks / Trade-offs

- [A stored document is less visible in a plain repository checkout] → retain a clear document name and use the existing `guide` category so Guide clients can discover it.
- [Curating loses useful detail] → retain only rules that express durable architectural or testing constraints, and preserve their intent without the personal-error framing.
