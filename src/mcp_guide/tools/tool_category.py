"""Category management tools."""

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.server import tools


class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool."""

    verbose: bool = True


@tools.tool(CategoryListArgs)
async def category_list(verbose: bool = True) -> str:
    """List all categories in the current project.

    Args:
        verbose: If True (default), return full category details; if False, return only names

    Returns:
        JSON string with Result containing:
        - If verbose=True: list of category dictionaries with name, dir, patterns, description
        - If verbose=False: list of category names only

    Example:
        >>> result = await category_list(verbose=True)
        >>> result_dict = json.loads(result)
        >>> if result_dict["success"]:
        ...     for cat in result_dict["value"]:
        ...         print(f"{cat['name']}: {cat['dir']}")
    """
    from mcp_guide.session import active_sessions

    sessions = active_sessions.get({})
    if not sessions:
        return Result.failure("No active session", error_type="no_session").to_json_str()

    session = next(iter(sessions.values()))

    project = await session.get_project()

    if verbose:
        categories: list[dict[str, str | list[str] | None]] = [
            {
                "name": category.name,
                "dir": category.dir,
                "patterns": list(category.patterns),
                "description": category.description,
            }
            for category in project.categories
        ]
    else:
        categories_list: list[str] = [category.name for category in project.categories]
        return Result.ok(categories_list).to_json_str()

    return Result.ok(categories).to_json_str()
