"""Helper function for processing and logging tool results before JSON conversion."""

from typing import TYPE_CHECKING, TypeVar

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.task_manager.manager import get_task_manager

if TYPE_CHECKING:
    from mcp_guide.result import Result

logger = get_logger(__name__)

T = TypeVar("T")


async def tool_result(tool_name: str, result: "Result[T]") -> str:
    """Process and log tool result before converting to JSON string.

    This function handles result processing that must occur before FastMCP's
    required JSON string conversion. It:
    1. Processes the result through TaskManager if available
    2. Logs the result at TRACE level for debugging
    3. Converts the result to JSON string for FastMCP

    Args:
        tool_name: Name of the tool that produced the result
        result: Result object to process and convert

    Returns:
        JSON string representation of the result for FastMCP

    Example:
        >>> result = Result.ok(value={"data": "example"})
        >>> return await tool_result("my_tool", result)
    """
    task_manager = get_task_manager()
    if task_manager is not None:
        try:
            result = await task_manager.process_result(result)
        except Exception as e:
            logger.error(f"TaskManager processing failed for tool {tool_name}: {e}")

    # Log result at TRACE level after TaskManager processing
    logger.trace(f"Tool '{tool_name}' result: {result.to_json()}")

    # Convert to JSON string for FastMCP
    return result.to_json_str()
