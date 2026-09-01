"""Shared MCP tool argument contract."""

from mcp_guide.core.arguments import Arguments as _Arguments

# ToolArguments is an identity alias for the shared Arguments type to preserve
# backwards compatibility with historical imports.
ToolArguments = _Arguments
Arguments = _Arguments


__all__ = ["ToolArguments", "Arguments"]
