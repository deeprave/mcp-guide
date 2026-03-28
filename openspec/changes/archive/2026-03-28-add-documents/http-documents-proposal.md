# Change: HTTP Document Ingestion

## Why

The document store can persist content from any source, and `send_file_content` already derives `source_type="url"` from HTTP prefixes. However there is no agent-facing command template to fetch a URL, convert the content to markdown, and ingest it. This is the missing piece for remote document support.

## What Changes

- Add `:document/add-url` command template that instructs the agent to:
  - Fetch URL content using whatever fetch capability is available (`web_fetch`, `fetch` from mcp-server-fetch, etc.)
  - Translate content to markdown with style driven by document type (see Translation Strategy below)
  - Extract `Last-Modified` header as mtime epoch float, falling back to current timestamp
  - Call `send_file_content` with `source=<url>` to trigger `source_type="url"` derivation

## Translation Strategy

The translation step always applies, regardless of whether the source returns HTML or markdown. Raw fetched content is the input, never the final output. The document type determines the translation style:

- `agent/instruction` — distill to directives. Strip preamble, non-instructive examples, navigation. Frame as imperative ("SHALL", "MUST"). Concise and succinct, AI-friendly.
- `agent/information` (default) — condense for AI consumption. Remove boilerplate, navigation, marketing. Keep all substantive points. Structured, no fluff.
- `user/information` — rewrite for human readability. Clean structure, clear headings, flowing prose. Keep examples and explanations. Remove only site chrome.

## Fetch Considerations

- The template should not hardcode a specific fetch tool. The agent knows what tools it has available.
- `web_fetch` and `mcp-server-fetch` both do HTTP GET with HTML→markdown conversion. Neither executes JavaScript.
- JS-rendered SPAs will return thin/empty content. The template should instruct the agent to warn the user if fetched content appears empty and suggest alternatives (different URL, paste content via `:document/add`).
- If the URL points directly to a `.md` file or raw content endpoint, the fetch result is already markdown — but the translation step still applies to reframe for intended use.
- `Accept: text/markdown` header is not practically useful; almost no sites honour it.

## mtime Strategy

- Use HTTP `Last-Modified` header parsed to epoch float when available
- Fall back to current timestamp when `Last-Modified` is absent
- Staleness relative to fetch time is as relevant as `Last-Modified` — both enable re-fetch detection
- mtime support is already plumbed through `send_file_content` → `DocumentTask` → document store

## Impact

- Affected specs: `document-commands` (MODIFIED)
- Affected code:
  - New `_commands/document/add-url.mustache` template
- Cross-reference: builds on `send_file_content` source_type derivation (`document_task.py:117`) and existing document store infrastructure from `add-documents`

## Supersedes

- `add-http-documents` (archived 2026-03-23) — server-side caching approach replaced by agent-driven fetch
- `add-client-documents` (archived 2026-03-23) — subsumed by `add-documents` store
