"""Prompts package.

Prompt Implementation Pattern
=============================

All prompts should follow this pattern for session access:

    from mcp_guide.session import get_current_session

    async def my_prompt(args: PromptArguments, ctx: Optional[Context] = None) -> dict:
        # Extract project name from context or args
        session = get_current_session(project_name)

        if session is None:
            return {"success": False, "error": "No active session"}

        project = await session.get_project()
        # Use project config...

        return {"success": True, "data": ...}

Note: Actual prompt implementations will be added as needed.
"""

# Import Arguments as PromptArguments for semantic clarity
from mcp_guide.core.arguments import Arguments as PromptArguments

__all__ = ["PromptArguments"]
