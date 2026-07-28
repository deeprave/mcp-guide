## Why

Agent detection currently advertises prompt syntax for clients that do not support prompts and does not recognise Aider. This produces instructions that the active agent cannot execute.

## What Changes

- Mark Cursor Agent as not supporting prompt invocation by returning `prompt_prefix=None`.
- Recognise Aider and configure its supported output and knowledge conventions.
- Audit the supported-agent table for other known clients and define explicit behavior for each supported or unsupported capability.

## Capabilities

### New Capabilities

- `agent-capability-support`: Model agent prompt and integration capabilities explicitly so rendered instructions match the client.

### Modified Capabilities

- `template-context`: Render agent-dependent command guidance only when the detected agent supports it.

## Impact

- Agent detection and formatting, agent knowledge directory mappings, template context, and tests.
