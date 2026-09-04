# See src/mcp_guide/tools/README.md for tool documentation standards

"""Utility tools for server information."""

from mcp_guide.agent_detection import format_agent_info
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_result import ToolResult, tool_result

logger = get_logger(__name__)

__all__ = ["internal_client_info"]


class GetClientInfoArgs(ToolArguments):
    """Arguments for client_info tool."""

    pass


async def internal_client_info(args: GetClientInfoArgs, request_context: RequestContext) -> Result[dict]:
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.

    Returns formatted agent information with explicit display instruction.

    Args:
        args: Tool arguments
        request_context: Resolved application request context

    Returns:
        Result containing agent information
    """
    try:
        session = request_context.session
        agent_info = session.agent_info

        if agent_info is None:
            return Result.failure("No client information available")

        # Build structured data
        from mcp_guide.core.prompt_decorator import get_prompt_name

        mcp_name = get_prompt_name()

        # For Claude: if mcp_name is "guide" (default), use "/" instead of "/guide:"
        if agent_info.normalized_name == "claude" and mcp_name == "guide":
            prompt_prefix = "/"
        elif agent_info.prompt_prefix is None:
            prompt_prefix = None
        else:
            prompt_prefix = agent_info.prompt_prefix.replace("{mcp_name}", mcp_name)

        data = {
            "agent": agent_info.name,
            "normalized_name": agent_info.normalized_name,
            "version": agent_info.version,
            "command_prefix": prompt_prefix,
        }

        # Use existing formatting function
        formatted = format_agent_info(agent_info, mcp_name)
        markdown = f"# MCP Client Information\n\n{formatted}"

        result = Result.ok(data)
        result.message = markdown
        return result
    except (AttributeError, KeyError, TypeError) as e:
        logger.exception("Error retrieving client info")
        return Result.failure(f"Error retrieving client info: {str(e)}")


@toolfunc(GetClientInfoArgs, requires_project=False)
async def client_info(args: GetClientInfoArgs, request_context: RequestContext) -> ToolResult:
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    """
    result = await internal_client_info(args, request_context)
    return await tool_result("client_info", result, session=request_context.session, session_id=args.session_id)
