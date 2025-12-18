"""Guide prompt implementation for direct content access."""

from typing import Any, Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_guide.prompts.guide_prompt_args import GuidePromptArguments
from mcp_guide.server import prompts
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content


@prompts.prompt(args_class=GuidePromptArguments)
async def guide(args: GuidePromptArguments, ctx: Optional[Any] = None) -> str:
    """Direct access to guide content without agent interpretation.

    Provides immediate access to project documentation and guides based on
    category or pattern matching. For MVP, uses the command parameter to
    call internal_get_content directly.

    Examples:
        @guide guide          - Get content from 'guide' category
        @guide lang/python    - Get content matching 'lang/python' pattern
        @guide                - Get help or default content
    """
    # Handle empty command gracefully
    if not args.command:
        return "Guide prompt usage: @guide <category_or_pattern>\n\nExamples:\n- @guide guide\n- @guide lang/python"

    # Call internal_get_content directly with the command as category_or_collection
    content_args = ContentArgs(category_or_collection=args.command, pattern=None)
    result = await internal_get_content(content_args, ctx)

    # Handle Result directly - no JSON parsing needed
    if result.success:
        return str(result.value)
    else:
        return f"Error: {result.error}"
