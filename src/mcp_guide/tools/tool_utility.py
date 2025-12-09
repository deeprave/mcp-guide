"""Utility tools for server information."""

import logging
from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.agent_detection import detect_agent, format_agent_info
from mcp_guide.guide import GuideMCP
from mcp_guide.server import tools
from mcp_guide.tools.tool_constants import INSTRUCTION_DISPLAY_ONLY

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

logger = logging.getLogger(__name__)


class GetClientInfoArgs(ToolArguments):
    """Arguments for get_client_info tool."""

    verbose: bool = Field(default=False, description="Unused parameter for compatibility")


@tools.tool(GetClientInfoArgs)
async def get_client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    Caches the result in GuideMCP for subsequent calls.

    Returns formatted agent information with explicit display instruction.

    Args:
        args: Tool arguments (verbose parameter is ignored)
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing agent information
    """
    try:
        if ctx is None:
            return Result.failure("Context not available").to_json_str()

        # Verify we have a GuideMCP instance
        if not isinstance(ctx.fastmcp, GuideMCP):
            return Result.failure("Server must be GuideMCP instance").to_json_str()

        mcp = ctx.fastmcp

        # Check cache
        if mcp.agent_info:
            agent_info = mcp.agent_info
        else:
            # Detect and cache
            if ctx.session.client_params is None:
                return Result.failure("No client information available").to_json_str()

            agent_info = detect_agent(ctx.session.client_params)
            mcp.agent_info = agent_info

        # Build structured data
        mcp_name = mcp.name if mcp.name else "guide"
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
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result.to_json_str()
    except (AttributeError, KeyError, TypeError) as e:
        logger.exception("Error retrieving client info")
        return Result.failure(f"Error retrieving client info: {str(e)}").to_json_str()
