# See src/mcp_guide/tools/README.md for tool documentation standards

"""Utility tools for server information."""

from typing import Optional

from pydantic import BaseModel, Field

from mcp_guide.agent_detection import detect_agent, format_agent_info
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.guide import GuideMCP
from mcp_guide.render.cache import invalidate_template_context_cache
from mcp_guide.result import Result
from mcp_guide.tools.tool_result import tool_result

try:
    from fastmcp import Context
except ImportError:
    Context = None  # ty: ignore[invalid-assignment]
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

        # Verify we have a GuideMCP instance
        if not isinstance(ctx.fastmcp, GuideMCP):
            return Result.failure("Server must be GuideMCP instance")

        # Read agent_info from session (populated during bootstrap by mcp_context.py)
        from mcp_guide.session import get_session

        session = await get_session(ctx)
        agent_info = session.agent_info

        if agent_info is None:
            # Not yet bootstrapped — detect now and store on session
            if ctx.session.client_params is None:
                return Result.failure("No client information available")

            cp = ctx.session.client_params
            normalized_cp = cp.model_dump() if isinstance(cp, BaseModel) else cp
            agent_info = detect_agent(normalized_cp)
            session.agent_info = agent_info
            session.client_params = normalized_cp
            invalidate_template_context_cache()

        # Build structured data
        mcp_name = ctx.fastmcp.name or "guide"

        # For Claude: if mcp_name is "guide" (default), use "/" instead of "/guide:"
        if agent_info.normalized_name == "claude" and mcp_name == "guide":
            prompt_prefix = "/"
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


@toolfunc(GetClientInfoArgs)
async def client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> str:
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    """
    result = await internal_client_info(args, ctx)
    return await tool_result("client_info", result)
