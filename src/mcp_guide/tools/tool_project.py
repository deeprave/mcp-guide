"""Project management tools."""

from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_constants import ERROR_NO_PROJECT, INSTRUCTION_NO_PROJECT

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class GetCurrentProjectArgs(ToolArguments):
    """Arguments for get_current_project tool."""

    verbose: bool = Field(default=False, description="If True, return full details; if False, return names only")


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

    collections: list[dict[str, str | list[str] | None]] | list[str]
    categories: list[dict[str, str | list[str] | None]] | list[str]

    if args.verbose:
        # Verbose: full details
        collections = [
            {"name": c.name, "description": c.description, "categories": c.categories} for c in project.collections
        ]
        categories = [
            {"name": c.name, "dir": c.dir, "patterns": list(c.patterns), "description": c.description}
            for c in project.categories
        ]
    else:
        # Non-verbose: names only
        collections = [c.name for c in project.collections]
        categories = [c.name for c in project.categories]

    result_dict = {"project": project.name, "collections": collections, "categories": categories}

    return Result.ok(result_dict).to_json_str()
