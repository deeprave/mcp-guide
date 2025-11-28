"""Example tool demonstrating tool conventions.

REQUIRES EXPLICIT USER INSTRUCTION to use this tool.
This tool is for demonstration purposes only.
"""

from typing import Any, Literal

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments


class ExampleArgs(ToolArguments):
    """Arguments for example tool."""

    action: Literal["demo", "test", "validate"]
    message: str = "Hello, World!"


@ToolArguments.declare
def example_tool(args: ExampleArgs) -> dict[str, Any]:
    """Example tool demonstrating all tool conventions.

    REQUIRES EXPLICIT USER INSTRUCTION: Only use when user explicitly requests
    to run the example tool or test tool conventions.

    This tool demonstrates:
    - ToolArguments base class with Pydantic validation
    - Literal types for constrained choices
    - Result[T] pattern for rich error handling
    - Instruction field for agent guidance
    - @ToolArguments.declare decorator for collection

    Args:
        args: Example arguments with action and message

    Returns:
        Result[dict] with demonstration data
    """
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
                "Tool collection via @declare",
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
