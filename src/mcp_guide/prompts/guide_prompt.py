"""Guide prompt implementation for direct content access."""

import json
from typing import Any, Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_guide.prompts.guide_prompt_args import GuidePromptArguments
from mcp_guide.server import prompts
from mcp_guide.tools.tool_content import get_content


@prompts.prompt(args_class=GuidePromptArguments)
async def guide(args: GuidePromptArguments, ctx: Optional[Any] = None) -> str:
    """Direct access to guide content without agent interpretation.

    Provides immediate access to project documentation and guides based on
    category or pattern matching. For MVP, uses the command parameter to
    call get_content directly.

    Examples:
        @guide guide          - Get content from 'guide' category
        @guide lang/python    - Get content matching 'lang/python' pattern
        @guide                - Get help or default content
    """
    # Handle empty command gracefully
    if not args.command:
        return "Guide prompt usage: @guide <category_or_pattern>\n\nExamples:\n- @guide guide\n- @guide lang/python"

    # Call get_content tool directly with the command as category_or_collection
    # will call _get_content after tool refactor and handle a Result instead of a stringified version
    from mcp_guide.tools.tool_content import ContentArgs

    content_args = ContentArgs(category_or_collection=args.command, pattern=None)
    result_json = await get_content(content_args, ctx)

    # get_content returns a JSON string, parse it to check for errors
    # Note: This manual JSON parsing is a temporary workaround that will be replaced when tool refactoring provides structured Result types
    try:
        result_data = json.loads(result_json)
        if result_data.get("success", False):
            return str(result_data.get("data", ""))
        else:
            return f"Error: {result_data.get('error', 'Unknown error')}"
    except json.JSONDecodeError:
        # If not valid JSON, return as-is (might be plain text error)
        return str(result_json)
