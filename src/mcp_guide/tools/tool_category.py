"""Category management tools."""

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.server import tools


class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool (currently no arguments needed)."""

    pass


@tools.tool(CategoryListArgs)
async def category_list() -> str:
    """List all categories in the current project.

    Returns a list of all categories with their configuration details including
    name, directory, patterns, and description (if available).

    Returns:
        JSON string with Result containing list of category dictionaries, each with:
        - name: Category name
        - dir: Directory path
        - patterns: List of glob patterns
        - description: Optional description (None if not available)

    Example:
        >>> result = await category_list()
        >>> result_dict = json.loads(result)
        >>> if result_dict["success"]:
        ...     for cat in result_dict["data"]:
        ...         print(f"{cat['name']}: {cat['dir']}")
    """
    from mcp_guide.session import active_sessions

    sessions = active_sessions.get({})
    if not sessions:
        return Result.failure("No active session", error_type="no_session").to_json_str()

    session = next(iter(sessions.values()))

    # Use proper async method - no encapsulation violation
    project = await session.get_project()

    categories = []
    for category in project.categories:
        categories.append(
            {
                "name": category.name,
                "dir": category.dir,
                "patterns": list(category.patterns),
                "description": getattr(category, "description", None),
            }
        )

    return Result.ok(categories).to_json_str()
