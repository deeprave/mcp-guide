"""Tools package.

Tool Implementation Pattern
===========================

All tools should follow this pattern for session access:

    from mcp_guide.result_constants import make_no_project_result
    from mcp_guide.tools.tool_helpers import get_session_and_project

    async def my_tool(ctx) -> dict:
        session, project = await get_session_and_project(ctx)
        if project is None:
            return await make_no_project_result(ctx)

        # Use project config...
        return {"success": True, "data": ...}
"""

# Import Arguments as ToolArguments for backward compatibility
from mcp_guide.core.arguments import Arguments as ToolArguments

# Import all tool modules to trigger @toolfunc decorators
from mcp_guide.tools import (  # noqa: F401
    tool_category,
    tool_collection,
    tool_content,
    tool_discovery,
    tool_document,
    tool_document_update,
    tool_feature_flags,
    tool_filesystem,
    tool_project,
    tool_resource,
    tool_update,
    tool_utility,
)
from mcp_guide.tools.tool_helpers import get_session_and_project
from mcp_guide.tools.tool_result import prompt_result, tool_result

__all__ = ["ToolArguments", "get_session_and_project", "tool_result", "prompt_result"]
