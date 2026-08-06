## Context

The server currently receives client filesystem information through MCP tools and routes it as task-manager events. `WorkflowMonitorTask` and `OpenSpecTask` therefore request or consume agent-relayed files even when a stdio server might be running from the same project directory as the client.

Transport type is insufficient evidence: HTTP(S) is treated as unshared, and stdio can still be launched from a different directory, container, or sandbox. The design must retain relay-first behavior until a particular stdio session proves access to the same project files.

## Goals / Non-Goals

**Goals:**

- Keep HTTP(S) and every unconfirmed session on the existing relay path.
- Confirm direct access only for stdio after the server working directory, client project directory, and initial workflow-file metadata agree.
- Use direct access for workflow state and OpenSpec discovery/version/change data only while that confirmation remains valid.
- Suppress all relay-oriented prompts, text, and reminders for data available by confirmed direct access.
- Fall back safely to agent relay if confirmation or direct reads fail.

**Non-Goals:**

- Treating stdio transport as shared by default.
- Broadening server filesystem permissions or allowing direct access outside the confirmed project directory.
- Removing filesystem relay tools; they remain the compatibility path.
- Implementing file watching for arbitrary client files.

## Decisions

### Default-deny, per-session direct access

Direct filesystem access begins disabled for every session. HTTP(S) remains permanently relay-only. A stdio session becomes eligible only after its client project directory is the same resolved path as server `Path.cwd()`.

### Confirmation uses an initial workflow-file ingest

The existing initial relay of the configured workflow file establishes confirmation. The server compares the agent-provided file metadata with its own `stat` result for the same resolved file: path is inside the confirmed project root, and modification time and size agree. A missing file, path mismatch, metadata mismatch, or read failure leaves the session unconfirmed.

This preserves the user-provided safety condition without relying on transport inference alone.

### Direct reads are narrow and revocable

Confirmed mode is limited to the workflow file and OpenSpec data rooted in the confirmed project directory. Each direct read applies existing path validation and freshness checks. Any failed validation, inaccessible file, changed root, or freshness disagreement revokes confirmed mode for the affected session and restores relay behavior.

### Prompt suppression follows the data source

Workflow and OpenSpec tasks consult the direct-access state before queuing setup prompts, version requests, change-list requests, or relay reminders. Templates receive the source state needed to avoid emitting `send_file_content` instructions for data already obtained directly. Suppression is scoped: unavailable data still uses the existing relay path.

## Risks / Trade-offs

- [A stdio process is launched outside the client project] → require resolved-root equality and initial file metadata agreement before enabling direct reads.
- [The project moves or server filesystem access changes] → revalidate the root and revoke direct mode on any failed read or mismatch.
- [Suppression hides a needed relay request] → suppress only after successful direct retrieval; otherwise immediately use existing prompts.
- [Direct reads bypass existing controls] → constrain reads to the confirmed root and retain existing filesystem security validation.
- [Per-session state leaks across HTTP clients] → store confirmation and direct-access caches in the existing project/session-scoped task lifecycle.

## Migration Plan

1. Ship with direct access disabled by default.
2. Enable it only after the stdio confirmation handshake succeeds.
3. Retain relay tools and prompts as fallback, with no configuration migration required.
4. Roll back by disabling or removing confirmation; all sessions revert to current relay behavior.

## Open Questions

- Whether matching mtime and size is sufficient across filesystems with coarse timestamp resolution, or whether a content digest is needed after the initial implementation proves a gap.
- Whether direct workflow change detection should use the existing timer cadence only or add a filesystem watcher within the confirmed project root.
