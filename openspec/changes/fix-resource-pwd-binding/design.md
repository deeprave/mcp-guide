# Design

## Context

Native resources check for a URI `session_id` before opening the shared request context. That bypasses the existing eligible-PWD bind used by tools and prompts. Generic resource templates also currently win over the command template for underscore-prefixed URIs.

## Goals / Non-Goals

**Goals:**

- Give eligible first native resource reads the same PWD bootstrap and continuation behaviour as tools and prompts.
- Route command URIs to their dedicated resource handler.

**Non-Goals:**

- Change PWD eligibility, non-stdio behaviour, or explicit `set_project`.
- Add new session identifiers or persistence.

## Decisions

- Enter the existing request-context scope before checking a missing resource session ID. Permit the resource only when it has an explicit URI ID or the scope reports that this request performed the eligible PWD bind. This reuses the established minting, binding, and response-continuation path without allowing a legacy connection's existing bound Session to bypass the explicit resource-ID rule.
- Register the underscore command resource before generic content templates so overlapping URIs select the dedicated command handler.
- Add one native MCP regression test: an eligible first `guide://_status` resource read succeeds and returns a session ID that a later resource URI can reuse.

## Risks / Trade-offs

- A legacy connection can already own a bound Session without a URI ID → retain the explicit-ID rule unless the scope records an actual PWD bind for this request.
