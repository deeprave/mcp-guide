"""Project management tools."""

from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.models import format_project_data
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session, set_project
from mcp_guide.tools.tool_constants import ERROR_NO_PROJECT, INSTRUCTION_NO_PROJECT

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class GetCurrentProjectArgs(ToolArguments):
    """Arguments for get_current_project tool."""

    verbose: bool = Field(default=False, description="If True, return full details; if False, return names only")


class SetCurrentProjectArgs(ToolArguments):
    """Arguments for set_current_project tool."""

    name: str = Field(description="Name of the project to switch to")
    verbose: bool = Field(
        default=False, description="If True, return full project details; if False, return simple confirmation"
    )


@tools.tool(GetCurrentProjectArgs)
async def get_current_project(args: GetCurrentProjectArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get information about the currently active project.

    Returns project name, collections, and categories. Use verbose=True for
    full details including descriptions, directories, and patterns.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing project information
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(
            str(e),
            error_type=ERROR_NO_PROJECT,
            instruction=INSTRUCTION_NO_PROJECT,
        ).to_json_str()

    project = await session.get_project()

    result_dict = format_project_data(project, verbose=args.verbose)

    return Result.ok(result_dict).to_json_str()


@tools.tool(SetCurrentProjectArgs)
async def set_current_project(args: SetCurrentProjectArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Switch to a different project by name.

    Creates new project with default categories if it doesn't exist. Use verbose=True
    for full project details after switching.

    Args:
        args: Tool arguments with name and verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing switch confirmation and optional project details
    """
    result = await set_project(args.name, ctx)

    if result.is_ok():
        project = result.value
        assert project is not None  # is_ok() guarantees value is set

        response = format_project_data(project, verbose=args.verbose)

        return Result.ok(response, message=f"Switched to project '{project.name}'").to_json_str()

    return result.to_json_str()
