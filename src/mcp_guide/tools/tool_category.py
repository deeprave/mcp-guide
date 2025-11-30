"""Category management tools."""

from typing import Optional

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description, validate_directory_path, validate_pattern
from mcp_guide.models import Category
from mcp_guide.server import tools

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool."""

    verbose: bool = True


@tools.tool(CategoryListArgs)
async def category_list(args: CategoryListArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all categories in the current project.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing:
        - If verbose=True: list of category dictionaries with name, dir, patterns, description
        - If verbose=False: list of category names only
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type="no_project").to_json_str()

    project = await session.get_project()

    if args.verbose:
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


class CategoryAddArgs(ToolArguments):
    """Arguments for category_add tool."""

    name: str
    dir: Optional[str] = None
    patterns: list[str] = []
    description: Optional[str] = None


@tools.tool(CategoryAddArgs)
async def category_add(
    name: str,
    dir: Optional[str] = None,
    patterns: list[str] = [],
    description: Optional[str] = None,
    ctx: Optional[Context] = None,  # type: ignore
) -> str:
    """Add a new category to the current project.

    Creates a new category with the specified name, directory, patterns, and optional description.
    The category is validated and saved to the project configuration immediately.

    Args:
        name: Category name (alphanumeric, dash, underscore only, max 30 chars)
        dir: Relative directory path for the category (defaults to name if omitted)
        patterns: List of glob patterns (defaults to empty list if omitted)
        description: Optional description (max 500 chars, no quotes)
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message

    Examples:
        >>> category_add(name="docs")
        >>> category_add(name="docs", dir="documentation", patterns=["*.md"])
        >>> category_add(name="api", dir="api", patterns=["*.py"], description="API docs")
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type="no_project").to_json_str()

    project = await session.get_project()

    try:
        if any(cat.name == name for cat in project.categories):
            raise ArgValidationError([{"field": "name", "message": f"Category '{name}' already exists"}])

        validated_dir = validate_directory_path(dir, default=name)
        validated_description = validate_description(description) if description else None

        for pattern in patterns:
            validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result().to_json_str()

    try:
        category = Category(name=name, dir=validated_dir, patterns=patterns, description=validated_description)
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result().to_json_str()

    try:
        await session.update_config(lambda p: p.with_category(category))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type="save_error").to_json_str()

    return Result.ok(f"Category '{name}' added successfully").to_json_str()
