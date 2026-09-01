# See src/mcp_guide/tools/README.md for tool documentation standards

"""Utility tools for server information."""

from typing import Optional

from fastmcp import Context
from pydantic import Field

from mcp_guide.agent_detection import detect_agent, format_agent_info
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.mcp_context import extract_client_params
from mcp_guide.render.cache import invalidate_template_context_cache
from mcp_guide.result import Result
from mcp_guide.tools.tool_result import ToolResult, tool_result

logger = get_logger(__name__)

__all__ = ["internal_client_info"]


class GetClientInfoArgs(ToolArguments):
    """Arguments for client_info tool."""

    verbose: bool = Field(default=False, description="Unused parameter for compatibility")


async def internal_client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> Result[dict]:
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.

    Returns formatted agent information with explicit display instruction.

    Args:
        args: Tool arguments (verbose parameter is ignored)
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing agent information
    """
    try:
        if ctx is None:
            return Result.failure("Context not available")

        # Read agent_info from session (populated during bootstrap by mcp_context.py)
        from mcp_guide.session import get_session

        session = await get_session(ctx, session_id=args.session_id)
        agent_info = session.agent_info

        if agent_info is None:
            # Not yet bootstrapped — detect now and store on session
            client_params = extract_client_params(ctx)
            if client_params is None:
                return Result.failure("No client information available")

            agent_info = detect_agent(client_params)
            session.agent_info = agent_info
            session.client_params = client_params
            invalidate_template_context_cache(session)

        # Build structured data
        from mcp_guide.core.prompt_decorator import get_prompt_name

        mcp_name = getattr(ctx.fastmcp, "name", None) or get_prompt_name()

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
async def client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    """
    result = await internal_client_info(args, ctx)
    return await tool_result("client_info", result, ctx=ctx, session_id=args.session_id)
