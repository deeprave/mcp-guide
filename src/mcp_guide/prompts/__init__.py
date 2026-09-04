"""Prompts package.

Prompt Implementation Pattern
=============================

All prompts receive the resolved application context:

    from mcp_guide.runtime import RequestContext

    async def my_prompt(args: PromptArguments, request_context: RequestContext) -> dict:
        project = request_context.project  # None when unbound
        # request_context.require_project() raises NoProjectError if unbound

        return {"success": True, "data": ...}

Note: Actual prompt implementations will be added as needed.
"""

# Import Arguments as PromptArguments for semantic clarity
from mcp_guide.core.arguments import Arguments as PromptArguments

__all__ = ["PromptArguments"]
