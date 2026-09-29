# Design

## Context

The request boundary already derives and retains a per-session protocol type:
`mcp_2026_07_28` for the current protocol and `legacy` for retained clients.
`client_info` currently formats cached client metadata without projecting that
classification, while the `_status` template renders client and workflow state
without it. See `proposal.md` for motivation and the delta specifications for
observable behaviour.

## Goals / Non-Goals

**Goals:**

- Project the established protocol classification as the `protocol` field of
  client information: in the `client_info` response and as `client.protocol`
  in template context.
- Use one human-readable representation consistently in both surfaces.
- Cover current-protocol and legacy-session behaviour.

**Non-Goals:**

- Changing protocol negotiation, session ownership, or protocol-specific result
  metadata adaptation.
- Exposing raw transport objects, public session identifiers, or a new client
  capability-negotiation API.
- Changing workflow state or feature-flag semantics.

## Decisions

### Reuse the retained session classification

Both surfaces will read the resolved session's immutable protocol type and map
it to the user-facing values `MCP 2026-07-28` and `legacy`. This avoids
re-parsing request headers or revisions at output time and prevents the two
surfaces from disagreeing.

The alternative—returning the raw negotiated revision—would expose a more
variable value and would not explicitly answer whether the client is in the
current or retained response-contract path.

### Store protocol in the client-information projection

The display-ready protocol value will be stored with the client-information
projection. The `client_info` tool returns it as `protocol`, while templates
receive it as `client.protocol`. `_status` renders that template variable rather
than duplicating protocol mapping in Mustache. This keeps the template
declarative and gives both output surfaces one presentation contract.

## Risks / Trade-offs

- [Two output paths drift in wording] → Centralise the display mapping and
  assert both rendered outputs for modern and legacy sessions.
- [Client metadata collection is disabled] → Retain the protocol field in the
  client-information projection because it comes from the established session,
  not optional client-data collection.

## Migration Plan

1. Add response and template-context coverage for both established protocol
   classifications before extending them.
2. Project the retained classification through the shared presentation path and
   update `client_info` and `_status` rendering.
3. Run focused tests for both surfaces and the existing protocol response
   adaptation coverage, followed by the relevant project checks.
4. Roll back by removing the additional optional presentation field; no stored
   state or client migration is required.
