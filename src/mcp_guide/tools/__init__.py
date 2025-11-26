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
