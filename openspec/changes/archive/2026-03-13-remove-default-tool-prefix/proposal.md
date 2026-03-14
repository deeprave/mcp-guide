# Change: Remove default tool prefix

## Why
Most MCP clients now namespace tools by server name automatically, making the `guide_` prefix redundant. The default should be no prefix; users who need a prefix can set `MCP_TOOL_PREFIX` explicitly.

## What Changes
- Change default tool prefix from `"guide"` to `""` (empty string) in `get_tool_prefix()` and `ServerConfig`
- Remove `--no-tool-prefix` CLI flag (redundant when default is already empty)
- Update CLI `--tool-prefix` help text to reflect new default
- Update `Environment Configuration` requirement in spec

## Impact
- Affected specs: `tool-infrastructure`
- Affected code: `src/mcp_guide/core/tool_decorator.py`, `src/mcp_guide/cli.py`
- Agents discover tools dynamically — no impact on agent behaviour
- Users with `MCP_TOOL_PREFIX=guide` set explicitly are unaffected
