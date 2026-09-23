## Why

Guide can advertise skills through its catalogue, but a catalogue does not tell
an agent which available action is relevant to the response it has just
received. Templates need a compact, structured way to recommend the next
Guide skill, tool, document, or expression without relying on prose parsing.

## What Changes

- Add a `recommend` template helper that renders fluent typed Guide references
and compact JSON footnotes directly into the returned document.
- Let templates explicitly recommend skills, commands, content, and tools;
unprefixed references default to content.
- Support rendered recommendation items for Guide skills, tools, documents, and
  content expressions without coupling the helper to a particular item type. A
  visible Guide-skill reference may use a footnote-style URI reference to keep
  the surrounding instruction fluent.
- Add a `{{tool_prefix}}use_skill` tool for MCP clients that cannot yet use
  Guide skills directly. It accepts a plain skill name (optionally prefixed by
  `$`) and forwards its tool arguments through shared skill resolution rather
  than duplicating skill rendering.

## Capabilities

### New Capabilities

- `recommend-items`: Template-authored rendered recommendations for Guide
actions and content.

### Modified Capabilities

- `template-support`: Templates can declare recommendations through the common
  `recommend` helper.

## Impact

- Template functions and document rendering.
- Tool registration and the shared skill-resource resolution path.
- Focused behaviour tests for rendered recommendations.
