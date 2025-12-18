"""Guide prompt implementation for direct content access."""

from typing import Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_core.result import Result
from mcp_guide.server import prompts
from mcp_guide.tools.tool_constants import INSTRUCTION_DISPLAY_ONLY
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content

# MCP compatibility limit for variable arguments
MAX_PROMPT_ARGS = 15


@prompts.prompt()
async def guide(
    arg1: Optional[str] = None,
    arg2: Optional[str] = None,
    arg3: Optional[str] = None,
    arg4: Optional[str] = None,
    arg5: Optional[str] = None,
    arg6: Optional[str] = None,
    arg7: Optional[str] = None,
    arg8: Optional[str] = None,
    arg9: Optional[str] = None,
    argA: Optional[str] = None,
    argB: Optional[str] = None,
    argC: Optional[str] = None,
    argD: Optional[str] = None,
    argE: Optional[str] = None,
    argF: Optional[str] = None,
    ctx: Optional["Context"] = None,  # type: ignore[type-arg]
) -> str:
    """Direct access to guide content without agent interpretation.

    Uses direct function parameters for MCP compatibility. Arguments are
    parsed into argv-style list: ["guide", arg1, arg2, ...] stopping at
    first None value.

    MCP clients send space-separated arguments:
    - @guide lang/python → arg1="lang/python"
    - @guide lang/python advanced → arg1="lang/python", arg2="advanced"

    Note: Uses MAX_PROMPT_ARGS (15) parameters due to MCP/FastMCP limitations
    with variable arguments (*args not supported for prompts).

    Args:
        arg1-argF: Optional string arguments (MAX_PROMPT_ARGS total)
        ctx: MCP context (auto-injected)

    Returns:
        JSON string with Result data
    """
    # Build argv list (stop at first None)
    argv = ["guide"]
    for arg in [arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, argA, argB, argC, argD, argE, argF]:
        if arg is None:
            break
        argv.append(arg)

    # Check if arguments provided
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == ""):  # No arguments or empty string
        result: Result[str] = Result.failure("Requires 1 or more arguments", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result.to_json_str()

    # Use first argument as category/pattern
    category = argv[1]
    content_args = ContentArgs(category_or_collection=category, pattern=None)
    content_result = await internal_get_content(content_args, ctx)

    # Set instruction and return as JSON
    content_result.instruction = INSTRUCTION_DISPLAY_ONLY
    return content_result.to_json_str()
