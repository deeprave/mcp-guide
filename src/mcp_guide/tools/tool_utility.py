# See src/mcp_guide/tools/README.md for tool documentation standards

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
        return result
    except (AttributeError, KeyError, TypeError) as e:
        logger.exception("Error retrieving client info")
        return Result.failure(f"Error retrieving client info: {str(e)}")


@tools.tool(GetClientInfoArgs)
async def client_info(args: GetClientInfoArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get information about the MCP client/agent.

    Captures agent name, version, and prompt prefix from the MCP session.
    Caches the result in GuideMCP for subsequent calls.

    ## JSON Schema

    ```json
    {
      "type": "object",
      "properties": {
        "verbose": {
          "type": "boolean",
          "description": "Unused parameter for compatibility"
        }
      }
    }
    ```

    ## Usage Instructions

    ```python
    # Get client information
    await client_info(GetClientInfoArgs())

    # With verbose parameter (ignored)
    await client_info(GetClientInfoArgs(verbose=True))
    ```

    ## Concrete Examples

    ```python
    # Example 1: Get MCP client details
    result = await client_info(GetClientInfoArgs())
    # Returns: {"agent_name": "Claude", "version": "3.5", "prompt_prefix": "guide"}

    # Example 2: Use for debugging or logging
    result = await client_info(GetClientInfoArgs(verbose=True))
    # Returns: Same information, verbose parameter is ignored for compatibility
    ```
    """
    return (await internal_client_info(args, ctx)).to_json_str()
