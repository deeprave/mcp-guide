"""Tools package.

Tool Implementation Pattern
===========================

All tools should follow this pattern for session access:

    from mcp_guide.session import get_current_session

    async def my_tool(project_name: str) -> dict:
        session = get_current_session(project_name)

        if session is None:
            return {"success": False, "error": "No active session"}

        project = await session.get_project()
        # Use project config...

        return {"success": True, "data": ...}

Note: Actual tool implementations will be added in separate changes.
"""

# Import Arguments as ToolArguments for backward compatibility
from mcp_guide.core.arguments import Arguments as ToolArguments

# Import all tool modules to trigger @toolfunc decorators
from mcp_guide.tools import (  # noqa: F401
    tool_category,
    tool_collection,
    tool_content,
    tool_discovery,
    tool_feature_flags,
    tool_filesystem,
    tool_project,
    tool_update,
    tool_utility,
)
from mcp_guide.tools.tool_result import prompt_result, tool_result

__all__ = ["ToolArguments", "tool_result", "prompt_result"]
