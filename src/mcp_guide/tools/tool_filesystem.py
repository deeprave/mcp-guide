"""Filesystem interaction tools for agent-server communication."""

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_core.tool_arguments import ToolArguments
from mcp_guide.filesystem.path_validator import SecurityError
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
) -> Result[Dict[str, Any]]:
    """Internal function to send file content from agent filesystem to server."""
    try:
        result = await fs_send_file_content(
            context=ctx,
            path=args.path,
            content=args.content,
            mtime=args.mtime,
            encoding=args.encoding,
        )
        return Result.ok(result)
    except FileNotFoundError as e:
        return Result.failure(error=f"File not found: {str(e)}", error_type="file_not_found")
    except PermissionError as e:
        return Result.failure(error=f"Permission denied: {str(e)}", error_type="permission_denied")
    except SecurityError as e:
        return Result.failure(error=f"Security violation: Path not allowed - {str(e)}", error_type="security_violation")
    except ConnectionError as e:
        return Result.failure(error=f"Communication error: {str(e)}", error_type="sampling_failure")
    except NotImplementedError as e:
        return Result.failure(
            error=f"Operation not supported: {str(e)}",
            error_type="unsupported_operation",
            instruction="Please upgrade your MCP client to support this feature",
        )
    except MemoryError as e:
        return Result.failure(error=f"Memory error: {str(e)}", error_type="resource_exhausted")
    except OSError as e:
        return Result.failure(error=f"Cache error: {str(e)}", error_type="cache_failure")
    except Exception as e:
        return Result.failure(error=f"Error processing file content: {str(e)}", error_type="unknown")


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
async def send_file_content(args: SendFileContentArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send file content from agent filesystem to server."""
    result = await internal_send_file_content(args, ctx)
    return result.to_json_str()


@tools.tool(SendDirectoryListingArgs)
async def send_directory_listing(args: SendDirectoryListingArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send directory listing from agent filesystem to server."""
    result = await internal_send_directory_listing(args, ctx)
    return result.to_json_str()


@tools.tool(SendCommandLocationArgs)
async def send_command_location(args: SendCommandLocationArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send command location from agent filesystem to server."""
    result = await internal_send_command_location(args, ctx)
    return result.to_json_str()


@tools.tool(SendWorkingDirectoryArgs)
async def send_working_directory(args: SendWorkingDirectoryArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Send working directory from agent filesystem to server."""
    result = await internal_send_working_directory(args, ctx)
    return result.to_json_str()
