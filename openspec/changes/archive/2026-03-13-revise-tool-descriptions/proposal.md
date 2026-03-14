# Change: Revise tool descriptions to concise standard

## Why
The current 4-section tool description standard has redundant and verbose sections:
- **Hand-written JSON Schema sections**: Docstrings contain manually-typed JSON Schema blocks that duplicate the auto-generated `## Arguments` block that `build_description` appends from Pydantic field descriptions at registration time
- **Usage Instructions and Concrete Examples**: Verbose format contrary to MCP best practice, which recommends concise 1-5 sentence descriptions
- **Inconsistent adoption**: 24 of 28 registered tools have minimal docstrings (3-12 lines) and don't follow the verbose standard

## What Changes
- Revise the standard: concise description only (2-4 sentences), no hand-written JSON Schema/Usage/Examples sections
- Update `src/mcp_guide/tools/README.md` template to reflect the revised standard
- Remove hand-written JSON Schema + Usage + Examples sections from the 4 verbose tools (`get_project`, `get_content`, `update_documents`, `client_info`) and replace with concise descriptions
- Improve descriptions for the 14 minimal tools (3-6 lines) to be clearer and more informative
- Optionally polish the 10 adequate tools (8-12 lines) for consistency
- Update `tool-infrastructure` spec to reflect the revised requirement
- **Keep**: Auto-generated `## Arguments` section from `build_description` - this remains the single source of parameter documentation

## Impact
- Affected specs: `tool-infrastructure`
- Affected code: `src/mcp_guide/tools/README.md` and all tool modules
- Non-breaking: tool behaviour unchanged, only docstrings change
- Agents still get full parameter documentation via auto-generated `## Arguments` section
