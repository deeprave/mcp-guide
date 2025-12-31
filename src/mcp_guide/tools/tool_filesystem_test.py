"""Test tools for filesystem interaction functionality."""

from pydantic import Field

from mcp_core.tool_arguments import ToolArguments
from mcp_core.tool_decorator import get_tool_prefix
from mcp_guide.result import Result
from mcp_guide.server import tools


class TestFilesystemReadArgs(ToolArguments):
    """Arguments for testing filesystem read functionality."""

    path: str = Field(description="File path to read from agent filesystem")


class TestFilesystemListArgs(ToolArguments):
    """Arguments for testing filesystem directory listing."""

    path: str = Field(description="Directory path to list from agent filesystem")


@tools.tool(TestFilesystemReadArgs)
async def test_filesystem_read(args: TestFilesystemReadArgs) -> str:
    """Test tool to request file content from agent filesystem."""
    return Result.ok(
        instruction=f"""
{get_tool_prefix()}send_file_content of the `{args.path}` text file.
Provide the absolute path of `{args.path}` file, the encoding and content.
"""
    ).to_json_str()


@tools.tool(TestFilesystemListArgs)
async def test_filesystem_list(args: TestFilesystemListArgs) -> str:
    """Test tool to request directory listing from agent filesystem."""
    return Result.ok(
        instruction=f"""
{get_tool_prefix()}send_directory_listing of regular files (only) in the `{args.path}` directory.
Provide the absolute path of the `{args.path}` directory and a list of each name, size, encoding and mtime in seconds of each entry.
"""
    ).to_json_str()
