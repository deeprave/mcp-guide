# Exploration: Efficient document ingestion

**Status**: Exploration
**Priority**: Low
**Complexity**: High

## Why

Document ingestion is currently too slow and too blocking to use comfortably, especially for batch imports. In common workflows a single ingest can take 30 to 60 seconds, and multi-document work compounds that delay.

The current path forces content through the agent:

1. acquire source content
2. prepare or relay that content
3. call `send_file_content`
4. let the server ingest and store the artifact

This creates two distinct issues:

- the user experience is often too blocking
- the stored artifact is not always optimized for later retrieval and use

This exploration therefore treats ingestion as more than a transport problem. It is about how to produce useful stored artifacts while making the workflow tolerable in real clients.

## What Changes

This exploration evaluates efficient document ingestion approaches before introducing any new import-specific commands or tools.

It focuses on:

- clarifying the true bottlenecks in document ingestion
- defining the default artifact model for stored documents
- separating local-file and URL ingestion concerns
- determining which clients can perform strict delegated ingestion end-to-end
- defining the optimized delegated and universal fallback behavior contracts
- producing a concrete recommendation for follow-on implementation work

## Current understanding

The exploration now supports several working conclusions:

- Stored documents should default to prepared knowledge artifacts for later use.
- `agent/information` should be the default target type for both local-file and URL ingestion.
- Raw storage should remain available, but as an explicit preservation mode rather than the default path.
- The server-side ingestion path appears shared and relatively lightweight.
- The main complexity and likely bottleneck live on the client side.
- Better UX is more likely to come from improved staging and handoff than from eliminating total work.

## Constraints

- The MCP server cannot assume access to the agent's filesystem. The server may run in Docker, over HTTP, on a different host, or in any environment isolated from the agent.
- Standard MCP tool usage requires the agent to mediate tool-to-tool data transfer. There is no portable MCP primitive that streams file content from one tool call to another without the agent participating.
- `send_file_content` is the critical final ingestion step. Any optimized delegated path must still be able to complete that step against the active MCP session.
- Agent and client capabilities differ materially. Some support delegation, subagents, or background work; others do not.
- Cloud-hosted background work is not sufficient by itself. If it cannot complete `send_file_content` into the active session, it does not satisfy the delegated-ingestion requirement.

## Target client matrix

The exploration explicitly considers:

- Kiro
- Kiro CLI
- Codex
- Codex App on macOS
- Claude Code
- Claude Desktop
- Cursor
- cursor-agent
- GitHub Copilot
- Gemini CLI
- opencode-ai
- Windsurf
- Cascade
- Cline

The current evidence suggests:

- **Tier 1 strong delegated-ingestion candidates**
  - Kiro / Kiro CLI
  - Claude Code
  - Codex local / in-session
- **Currently out for strict delegated ingestion**
  - Codex cloud
  - GitHub Copilot
  - Cursor / cursor-agent
  - Claude Desktop
  - Windsurf / Cascade
  - opencode-ai
  - Gemini CLI
  - Cline

This classification is specifically about end-to-end delegated ingestion, not about general agent quality.

Codex local / in-session was initially treated as conditional, but a direct background-worker test in Codex local behaved as desired: it created a separate worker, completed the requested work without blocking the main interaction, produced the requested output file, and later reported completion successfully. That is strong enough to keep Codex local in scope for first-pass optimized support.

Cursor / cursor-agent was initially kept as a conditional candidate because its documented background-agent model looked promising. A stricter retry that explicitly required true background execution and actual file writing returned `BACKGROUND_UNAVAILABLE`, and no file was written. That is strong enough to treat Cursor as fallback-only for now unless a different Cursor-specific workflow is found and validated.

## Exploration goals

This change does not assume that "background import" is the correct solution. It explores the broader problem of how to make ingestion effective, useful, and tolerable.

The exploration should answer:

1. Which costs matter most:
   - foreground blocking time,
   - total completion time,
   - context/token overhead,
   - artifact usefulness,
   - or operator effort?
2. What should the system store by default:
   - raw source material,
   - or prepared knowledge artifacts?
3. What is the right split between:
   - local-file acquisition and preparation,
   - URL acquisition and preparation,
   - and shared server-side ingestion?
4. Which clients can truly perform delegated ingestion end-to-end, including `send_file_content`?
5. What fallback behavior is required when optimized delegated execution is unavailable?

## Candidate approach families

The exploration should compare multiple architectural families:

- Baseline inline ingestion with clearer guidance
- Prepared-by-default ingestion using existing commands and better templates
- Delegated/background ingestion for clients that can complete end-to-end ingestion
- Helper abstractions that prepare manifests or structured task descriptions
- Alternative transport or batching ideas that reduce relay cost
- Platform-specific optimizations with explicit fallback

## Non-goals for this change

- Committing to a specific new command shape such as `document/import`
- Assuming that moving work into the background solves total throughput
- Assuming all clients with background work qualify for delegated ingestion
- Designing around cloud-hosted background agents that cannot complete `send_file_content` into the active session

## Key research questions

- What minimum client capability is required for a true delegated-ingestion path?
- Can one shared optimized delegated branch support both Kiro and Claude Code with only small wording differences?
- Should the optimized branch describe only the behavior contract and let the client choose the native mechanism?
- How should raw mode behave for local files, remote text, and remote sources that require conversion?
- Which conclusions are strong enough to capture in OpenSpec now, and which still need more client validation?

## Expected outcome

This exploration should produce:

1. A validated understanding of the ingestion pipeline and where the real bottlenecks are
2. A clearer product stance on prepared artifacts versus raw preservation
3. A client matrix focused on strict delegated-ingestion feasibility
4. A behavior contract for:
   - optimized delegated ingestion
   - universal inline fallback
5. A recommendation for whether to proceed with:
   - no product change,
   - improved workflow guidance,
   - a narrow Tier-1 optimized path with fallback,
   - or a broader follow-up change once more clients are validated

## Outcome

This exploration is complete.

Its findings resulted in the follow-on implementation change:

- `improve-ux-documents`

The recommendation outcome was:

- proceed with a narrow Tier-1 optimized path plus universal fallback
- exploit those findings for document ingestion and export UX improvements in `improve-ux-documents`
- treat the exploration as complete once its findings were captured and carried forward
