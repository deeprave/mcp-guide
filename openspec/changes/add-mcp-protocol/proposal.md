# Proposal

## Why

Guide already distinguishes connected clients using MCP `2026-07-28` from retained legacy clients internally, but agents cannot inspect that distinction through either `client_info` or the status command. Exposing the active connection protocol makes protocol-dependent response behaviour diagnosable without relying on server logs.

## What Changes

- Save the connected session's public protocol classification as the `protocol` field of client information, distinguishing MCP `2026-07-28` from legacy clients.
- Return that `protocol` field from the `client_info` tool and expose it to templates as `client.protocol` alongside other client information.
- Render `client.protocol` in the `_status` command.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tool-infrastructure`: `client_info` reports the established session's protocol classification alongside available client environment details.
- `workflow-context`: the `_status` command template reports the connected session's protocol classification with its workflow and project status.

## Impact

- Affected code: the `client_info` tool, request/session context projection, and `_status` command template context and rendering.
- Affected tests: tool-result and status-command template coverage for both MCP `2026-07-28` and legacy sessions.
- No new dependencies, protocol negotiation rules, or changes to the existing protocol-specific response adaptation contract.
