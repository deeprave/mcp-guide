"""Filesystem interaction tools for agent-server communication."""

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_core.tool_arguments import ToolArguments
from mcp_guide.filesystem.tools import send_command_location as fs_send_command_location
from mcp_guide.filesystem.tools import send_directory_listing as fs_send_directory_listing
from mcp_guide.filesystem.tools import send_file_content as fs_send_file_content
from mcp_guide.filesystem.tools import send_working_directory as fs_send_working_directory
from mcp_guide.result import Result
from mcp_guide.server import tools


class SendFileContentArgs(ToolArguments):
    """Arguments for sending file content from agent to server."""

    path: str = Field(description="File path that was requested")
    content: str = Field(description="File content from agent's filesystem")
    mtime: Optional[float] = Field(default=None, description="File modification time")
    encoding: str = Field(default="utf-8", description="File encoding")


class SendDirectoryListingArgs(ToolArguments):
    """Arguments for sending directory listing from agent to server."""

    path: str = Field(description="Directory path that was requested")
    entries: list[Dict[str, Any]] = Field(description="Directory entries with name, type, size, mtime")


class SendCommandLocationArgs(ToolArguments):
    """Arguments for sending command location from agent to server."""

    command: str = Field(description="Command name that was requested")
    location: Optional[str] = Field(description="Full path to command, or None if not found")


class SendWorkingDirectoryArgs(ToolArguments):
    """Arguments for sending working directory from agent to server."""

    path: str = Field(description="Current working directory path")


async def internal_send_file_content(
    args: SendFileContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> "Result[dict[str, Any]]":
    """Internal function to send file content from agent filesystem to server."""
    return await fs_send_file_content(
        context=ctx,
        path=args.path,
        content=args.content,
        mtime=args.mtime,
        encoding=args.encoding,
    )


async def internal_send_directory_listing(
    args: SendDirectoryListingArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[Dict[str, Any]]:
    """Internal function to send directory listing from agent filesystem to server."""
    try:
        result = await fs_send_directory_listing(
            context=ctx,
            path=args.path,
            files=args.entries,
        )
        return Result.ok(result)
    except Exception as e:
        return Result.failure(error=f"Error processing directory listing: {str(e)}", error_type="unknown")


async def internal_send_command_location(
    args: SendCommandLocationArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[Dict[str, Any]]:
    """Internal function to send command location from agent filesystem to server."""
    try:
        result = await fs_send_command_location(
            context=ctx,
            command=args.command,
            path=args.location,
            found=args.location is not None,
        )
        return Result.ok(result)
    except Exception as e:
        return Result.failure(error=f"Error processing command location: {str(e)}", error_type="unknown")


async def internal_send_working_directory(
    args: SendWorkingDirectoryArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[Dict[str, Any]]:
    """Internal function to send working directory from agent filesystem to server."""
    try:
        result = await fs_send_working_directory(
            context=ctx,
            working_directory=args.path,
        )
        return Result.ok(result)
    except Exception as e:
        return Result.failure(error=f"Error processing working directory: {str(e)}", error_type="unknown")


@tools.tool(SendFileContentArgs)
async def send_file_content(args: SendFileContentArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Send file content from agent filesystem to server."""
    result = await internal_send_file_content(args, ctx)

    # Process through TaskManager before converting to JSON
    # Import here to avoid circular dependency with tool_decorator module
    from mcp_core.tool_decorator import _task_manager
    from mcp_guide.task_manager.interception import FSEventType

    if _task_manager is not None:
        result = await _task_manager.process_result(result, FSEventType.FILE_CONTENT)

    return result.to_json_str()


@tools.tool(SendDirectoryListingArgs)
async def send_directory_listing(args: SendDirectoryListingArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send directory listing from agent filesystem to server."""
    result = await internal_send_directory_listing(args, ctx)

    # Process through TaskManager before converting to JSON
    from mcp_core.tool_decorator import _task_manager
    from mcp_guide.task_manager.interception import FSEventType

    if _task_manager is not None:
        result = await _task_manager.process_result(result, FSEventType.DIRECTORY_LISTING)

    return result.to_json_str()


@tools.tool(SendCommandLocationArgs)
async def send_command_location(args: SendCommandLocationArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send command location from agent filesystem to server."""
    result = await internal_send_command_location(args, ctx)

    # Process through TaskManager before converting to JSON
    from mcp_core.tool_decorator import _task_manager
    from mcp_guide.task_manager.interception import FSEventType

    if _task_manager is not None:
        result = await _task_manager.process_result(result, FSEventType.COMMAND_LOCATION)

    return result.to_json_str()


@tools.tool(SendWorkingDirectoryArgs)
async def send_working_directory(args: SendWorkingDirectoryArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send working directory from agent filesystem to server."""
    result = await internal_send_working_directory(args, ctx)

    # Process through TaskManager before converting to JSON
    from mcp_core.tool_decorator import _task_manager
    from mcp_guide.task_manager.interception import FSEventType

    if _task_manager is not None:
        result = await _task_manager.process_result(result, FSEventType.WORKING_DIRECTORY)

    return result.to_json_str()
