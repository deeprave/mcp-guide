"""Collection management tools."""

from typing import Any, Optional

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


# Common error types
ERROR_NO_PROJECT = "no_project"


class CollectionListArgs(ToolArguments):
    """Arguments for collection_list tool."""

    verbose: bool = True


@tools.tool(CollectionListArgs)
async def collection_list(args: CollectionListArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all collections in the current project.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing:
        - If verbose=True: list of collection dictionaries with name, categories, description
        - If verbose=False: list of collection names only
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    collections: Any
    if args.verbose:
        collections = [
            {
                "name": collection.name,
                "categories": list(collection.categories),
                "description": collection.description,
            }
            for collection in project.collections
        ]
    else:
        collections = [collection.name for collection in project.collections]

    return Result.ok(collections).to_json_str()
