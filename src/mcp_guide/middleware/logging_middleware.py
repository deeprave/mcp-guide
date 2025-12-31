"""Logging middleware for command execution."""

from typing import Awaitable, Callable, Union

from mcp_core.mcp_log import get_logger
from mcp_guide.result import Result

logger = get_logger(__name__)


async def logging_middleware(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    next_handler: Callable[[], Awaitable[Result[str]]],
) -> Result[str]:
    """Log command usage and responses."""
    logger.debug(f"Executing command: {command_path} with args={args} kwargs={kwargs}")

    result = await next_handler()

    if result.success:
        logger.debug(f"Command {command_path} succeeded with {len(result.value or '')} chars")
    else:
        logger.debug(f"Command {command_path} failed: {result.error}")

    return result
