# Change: Add export_content tool for knowledge indexing

## Why
Agents normally consume content via `get_content`, which dumps the full document text into the context window. Kiro and kiro-cli support a "knowledge" indexing mechanism that allows documents to be semantically queried using a tiny fraction of the context window. This change adds `export_content` — identical to `get_content` but with an export path argument — which returns the content to the agent along with an instruction to write it to the specified path for knowledge indexing.

The MCP server cannot write to the agent's filesystem directly; the agent performs the write based on the instruction in the response.

## What Changes
- New `export_content` tool: same `expression` + optional `pattern` interface as `get_content`
- Additional arguments: `path` (required, must be in project `allowed_write_paths`) and `force` (default `False`)
- Returns full content plus an instruction directing the agent to write the content to `path`
- If `force=False` and file exists at path, instruction indicates create-only (agent should not overwrite)
- If `force=True`, instruction indicates forced overwrite is permitted
- Path is validated against project `allowed_write_paths` before content is returned
- Add `.kiro/knowledge/` to `DEFAULT_ALLOWED_WRITE_PATHS` so it is available without manual configuration
- Omit `allowed_write_paths` from project config serialization when it equals the default (avoid redundant storage)
- New capability spec: `knowledge-export`

## Impact
- Affected specs: new `knowledge-export` spec, `project-config` (modified serialization)
- Affected code: `src/mcp_guide/models/constants.py`, `src/mcp_guide/session.py` (`_project_to_dict`)
- Non-breaking: `get_content` unchanged; existing configs with explicit `allowed_write_paths` are unaffected
- No manifest or suppression logic needed — agent manages its own knowledge state
