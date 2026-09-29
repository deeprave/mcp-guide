# Tasks

## 1. Protocol presentation contract

- [x] 1.1 Add a shared display projection for an established session's `mcp_2026_07_28` and `legacy` protocol types, and verify unit coverage includes both classifications.
- [x] 1.2 Store the classification as client-information field `protocol`, return it from `client_info`, and verify focused utility and integration tests cover modern and legacy sessions.

## 2. Status command rendering

- [x] 2.1 Add the protocol display value to template context as `client.protocol` alongside other client-information fields, and verify context/rendering tests cover enabled and disabled workflow states.
- [x] 2.2 Render `client.protocol` in the `_status` command, and verify rendered-output tests distinguish MCP `2026-07-28` and legacy protocol information.

## 3. Regression validation

- [x] 3.1 Run focused protocol-adaptation, utility-tool, and status-template tests, and verify existing modern and legacy response metadata contracts remain unchanged.
- [x] 3.2 Run the required project checks and `openspec validate add-mcp-protocol --strict`, and verify the completed implementation conforms to the proposal, design, and delta specifications.
