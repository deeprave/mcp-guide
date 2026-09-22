## Why

Guide can advertise skills through its catalogue, but a catalogue does not tell
an agent which available action is relevant to the response it has just
received. Templates need a compact, structured way to recommend the next
Guide skill, tool, document, or expression without relying on prose parsing.

## What Changes

- Add a `recommend` template helper that records a rendered recommendation
  while omitting its marker from ordinary rendered content.
- Establish an explicit `Guide skill "<name>"` recommendation form, so
  templates can direct an agent to the correct skill before the Git workflow
  templates are refactored. Its metadata includes a `guide://$<name>` resource
  fallback, without making that URI the primary instruction.
- Deliver recorded recommendations as structured response metadata, preserving
  the existing text and instruction contracts when no recommendation is made.
- Support rendered recommendation items for Guide skills, tools, documents, and
  content expressions without coupling the helper to a particular item type. A
  visible Guide-skill reference may use a footnote-style URI reference to keep
  the surrounding instruction fluent.
- Add a feature-gated startup partial that contributes Guide-skill suggestions
  when the global `mcp-skills` experiment is enabled.

## Capabilities

### New Capabilities

- `recommend-items`: Template-authored, structured recommendations for Guide
  actions and content.

### Modified Capabilities

- `guide-url-skills`: Startup delivery can advertise template-authored Guide
  skill suggestions when the optional MCP skills extension is enabled.
- `response-metadata`: Responses carry structured recommendations without
  changing existing instruction delivery.
- `template-support`: Templates can declare recommendations through the common
  `recommend` helper.

## Impact

- Template functions, rendered-content models, and MCP response adapters.
- Startup templates and the optional Guide skills extension path.
- Focused behaviour tests for recommendation capture, structured delivery, and
  feature-gated startup suggestions.
