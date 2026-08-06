## Why

Guide currently relies on an agent to relay workflow and OpenSpec filesystem data to the MCP server. In a stdio deployment the server may share the client project filesystem, making that relay unnecessary, but transport mode alone is not trustworthy evidence. A confirmed direct-access mode can remove redundant requests without weakening the safe default for remote or unconfirmed environments.

## What Changes

- Define a conservative shared-filesystem confirmation flow for stdio sessions.
- Keep HTTP(S) sessions and unconfirmed stdio sessions on the existing agent-relay path.
- Allow confirmed shared-filesystem sessions to read the configured workflow file and OpenSpec metadata directly from the server filesystem.
- Suppress file-relay prompts, instructions, and monitoring reminders only for information successfully available through confirmed direct access.
- Fall back to relay behavior if confirmation, a direct read, or freshness validation fails.

## Capabilities

### New Capabilities

- `stdio-direct-filesystem`: Confirm a shared filesystem for a stdio session and safely select direct server reads only after confirmation.

### Modified Capabilities

- `filesystem-interaction`: Preserve relay tools as the default and define their suppression/fallback behavior in confirmed direct-access sessions.
- `workflow-monitoring`: Source workflow state directly after confirmation and avoid relay-only workflow prompts when it is available.
- `template-context`: Expose direct-access availability and fresh workflow/OpenSpec state consistently to template rendering.

## Impact

- Transport and session capability detection.
- Filesystem ingestion and path/freshness validation.
- Workflow and OpenSpec tasks, their instruction templates, and task-manager cache invalidation.
- Tests for HTTP(S), unconfirmed stdio, confirmed stdio, direct-read failure, and fallback behavior.
