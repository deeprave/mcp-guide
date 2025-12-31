"""Example tool demonstrating tool conventions.

REQUIRES EXPLICIT USER INSTRUCTION to use this tool.
This tool is for demonstration purposes only.
"""

from typing import Any, Literal, Optional

from mcp_core.tool_arguments import ToolArguments
from mcp_guide.result import Result
from mcp_guide.server import tools

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class ExampleArgs(ToolArguments):
    """Arguments for example tool."""

    action: Literal["demo", "test", "validate"]
    message: str = "Hello, World!"


@tools.tool(ExampleArgs)
async def example_tool(args: ExampleArgs, ctx: Optional[Context] = None) -> dict[str, Any]:  # type: ignore
    """Example tool demonstrating all tool conventions.

    REQUIRES EXPLICIT USER INSTRUCTION: Only use when user explicitly requests
    to run the example tool or test tool conventions.

    This tool demonstrates:
    - ToolArguments base class with Pydantic validation
    - Literal types for constrained choices
    - Result[T] pattern for rich error handling
    - Instruction field for agent guidance
    - Decorator-based registration
    - Context parameter for MCP capabilities

    Args:
        args: Example arguments with action and message
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result[dict] with demonstration data
    """
    # Log using context if available
    if ctx is not None:
        await ctx.info(f"Example tool invoked with action={args.action}, message={args.message}")

    # Demonstrate Result pattern with instruction field
    result = Result.ok(
        {
            "action": args.action,
            "message": args.message,
            "conventions_demonstrated": [
                "ToolArguments base class",
                "Literal type constraints",
                "Result[T] pattern",
                "Instruction field",
                "Decorator-based registration",
                "Context parameter usage",
            ],
        }
    )

    # Add instruction for agent
    result.instruction = (
        "This is an example tool. In production tools, use the instruction field to:\n"
        "- Prevent automatic remediation attempts\n"
        "- Suggest specific fixes\n"
        "- Control agent behavior\n"
        "- Provide context-specific guidance"
    )

    return result.to_json()
