# See src/mcp_guide/tools/README.md for tool documentation standards

"""Utility tools for server information."""

from typing import Optional

from pydantic import Field

from mcp_guide.agent_detection import detect_agent, format_agent_info
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.guide import GuideMCP
from mcp_guide.render.cache import invalidate_template_context_cache
from mcp_guide.result import Result
from mcp_guide.tools.tool_result import tool_result

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

logger = get_logger(__name__)

__all__ = ["internal_client_info"]


class GetClientInfoArgs(ToolArguments):
    """Arguments for client_info tool."""

    verbose: bool = Field(default=False, description="Unused parameter for compatibility")


async def internal_client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> Result[dict]:  # type: ignore[type-arg]
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    Caches the result in GuideMCP for subsequent calls.

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

        mcp = ctx.fastmcp

        # Check cache
        if mcp.agent_info:
            agent_info = mcp.agent_info
        else:
            # Detect and cache
            if ctx.session.client_params is None:
                return Result.failure("No client information available")

            agent_info = detect_agent(ctx.session.client_params)
            mcp.agent_info = agent_info

            # Invalidate template cache so next render picks up agent info
            invalidate_template_context_cache()

            # Update cached_mcp_context with agent info
            from time import time

            from mcp_guide.mcp_context import CachedMcpContext, get_cached_mcp_context, set_cached_mcp_context

            existing = get_cached_mcp_context()
            set_cached_mcp_context(
                CachedMcpContext(
                    roots=existing.roots if existing else [],
                    project_name=existing.project_name if existing else "",
                    agent_info=agent_info,
                    client_params=ctx.session.client_params,
                    timestamp=time(),
                )
            )

        # Build structured data
        mcp_name = mcp.name if mcp.name else "guide"

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
async def client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    Caches the result in GuideMCP for subsequent calls.
    """
    result = await internal_client_info(args, ctx)
    return await tool_result("client_info", result)
