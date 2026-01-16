"""Tool arguments - alias for Arguments base class."""

# Import Arguments as ToolArguments for backward compatibility
from mcp_guide.core.arguments import Arguments as ToolArguments

# Re-export for existing imports
__all__ = ["ToolArguments"]
