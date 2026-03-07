# Change: Revise tool descriptions to concise standard

## Why
The current 4-section tool description standard requires a manually-written JSON Schema section that is redundant — `build_description` already auto-appends a `## Arguments` block generated from Pydantic field descriptions at registration time. The verbose format (JSON Schema + Usage Instructions + Concrete Examples) is also contrary to MCP best practice, which recommends concise 1-5 sentence descriptions. 24 of 28 registered tools have minimal or one-liner docstrings and are non-compliant with the current standard.

## What Changes
- Revise the standard: concise description only (no JSON Schema section; Usage/Examples optional for complex tools)
- Update `src/mcp_guide/tools/README.md` template to reflect the revised standard
- Remove JSON Schema sections from the 4 tools that have them (`get_project`, `get_content`, `update_documents`, `client_info`) and replace with concise descriptions
- Write good concise descriptions for the 24 tools with minimal/one-liner docstrings
- Fix `list_profiles` docstring: move content from `internal_list_profiles` to the registered `list_profiles` function
- Update `tool-infrastructure` spec to reflect the revised requirement

## Impact
- Affected specs: `tool-infrastructure`
- Affected code: `src/mcp_guide/tools/README.md` and all tool modules
- Non-breaking: tool behaviour unchanged, only docstrings change
- `build_description` retained — it still appends the auto-generated `## Arguments` block from Pydantic field descriptions
