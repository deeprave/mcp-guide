## Why

Agent detection currently advertises prompt syntax for clients that do not support prompts and does not recognise Pi. This produces instructions that the active agent cannot execute.

## What Changes

- Make `prompt_prefix=None` the default; retain explicit prompt prefixes only for clients with verified prompt support, including Cursor and Pi as prompt-incapable clients.
- Recognise Pi and canonicalise Pi MCP Guide client names such as `pi-mcp-guide` to `pi`.
- Audit the supported-agent table for other known clients and define explicit behavior for each supported or unsupported capability.

## Capabilities

### New Capabilities

- `agent-capability-support`: Model agent prompt and integration capabilities explicitly so rendered instructions match the client.

### Modified Capabilities

- `template-context`: Render agent-dependent command guidance only when the detected agent supports it.

## Impact

- Agent detection and formatting, template context, and tests.
