"""Category management tools."""

from dataclasses import replace
from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description, validate_directory_path, validate_pattern
from mcp_guide.models import Category, Project
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
    patterns: list[str] = Field(default_factory=list)
    description: Optional[str] = None


@tools.tool(CategoryAddArgs)
async def category_add(
    name: str,
    dir: Optional[str] = None,
    patterns: Optional[list[str]] = None,
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

    patterns = patterns or []

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
        # ValueError can only come from Category.name validation (other fields validated above)
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result().to_json_str()

    try:
        await session.update_config(lambda p: p.with_category(category))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type="save_error").to_json_str()

    return Result.ok(f"Category '{name}' added successfully").to_json_str()


class CategoryRemoveArgs(ToolArguments):
    """Arguments for category_remove tool."""

    name: str


@tools.tool(CategoryRemoveArgs)
async def category_remove(
    name: str,
    ctx: Optional[Context] = None,  # type: ignore
) -> str:
    """Remove a category from the current project.

    Removes the specified category and automatically removes it from all collections.
    Changes are saved to the project configuration immediately.

    Args:
        name: Name of the category to remove
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message

    Examples:
        >>> category_remove(name="docs")
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type="no_project").to_json_str()

    project = await session.get_project()

    if not any(cat.name == name for cat in project.categories):
        return Result.failure(f"Category '{name}' does not exist", error_type="not_found").to_json_str()

    def remove_category_and_update_collections(p: Project) -> Project:
        p_without_cat = p.without_category(name)
        updated_collections = [
            replace(col, categories=[c for c in col.categories if c != name]) for col in p_without_cat.collections
        ]
        return replace(p_without_cat, collections=updated_collections)

    try:
        await session.update_config(remove_category_and_update_collections)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type="save_error").to_json_str()

    return Result.ok(f"Category '{name}' removed successfully").to_json_str()


class CategoryChangeArgs(ToolArguments):
    """Arguments for category_change tool."""

    name: str
    new_name: Optional[str] = None
    new_dir: Optional[str] = None
    new_patterns: Optional[list[str]] = None
    new_description: Optional[str] = None


@tools.tool(CategoryChangeArgs)
async def category_change(
    name: str,
    new_name: Optional[str] = None,
    new_dir: Optional[str] = None,
    new_patterns: Optional[list[str]] = None,
    new_description: Optional[str] = None,
    ctx: Optional[Context] = None,  # type: ignore
) -> str:
    """Change properties of an existing category.

    Can change name (with collection updates), dir, patterns, or description.
    At least one new value must be provided.
    Changes are saved to the project configuration immediately.

    Args:
        name: Current name of the category to change
        new_name: New name for the category (updates collections)
        new_dir: New directory path
        new_patterns: New patterns list (replaces all patterns)
        new_description: New description (empty string clears it)
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message

    Examples:
        >>> category_change(name="docs", new_name="documentation")
        >>> category_change(name="docs", new_dir="documentation")
        >>> category_change(name="docs", new_description="Updated docs")
        >>> category_change(name="docs", new_patterns=["*.md", "*.txt"])
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type="no_project").to_json_str()

    project = await session.get_project()

    existing_category = next((c for c in project.categories if c.name == name), None)
    if existing_category is None:
        return Result.failure(f"Category '{name}' does not exist", error_type="not_found").to_json_str()

    if new_name is None and new_dir is None and new_patterns is None and new_description is None:
        return (
            ArgValidationError(
                [
                    {
                        "field": "changes",
                        "message": "At least one change must be provided (new_name, new_dir, new_patterns, or new_description)",
                    }
                ]
            )
            .to_result()
            .to_json_str()
        )

    try:
        if new_name is not None:
            if any(c.name == new_name for c in project.categories if c.name != name):
                raise ArgValidationError([{"field": "new_name", "message": f"Category '{new_name}' already exists"}])

        if new_dir is not None:
            if new_dir == "":
                raise ArgValidationError([{"field": "new_dir", "message": "Directory path cannot be empty"}])
            validate_directory_path(new_dir, default=new_dir)

        if new_description is not None and new_description != "":
            validate_description(new_description)

        if new_patterns is not None:
            for pattern in new_patterns:
                validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result().to_json_str()

    if new_description == "":
        final_description = None
    elif new_description is not None:
        final_description = new_description
    else:
        final_description = existing_category.description

    try:
        updated_category = Category(
            name=new_name if new_name is not None else existing_category.name,
            dir=new_dir if new_dir is not None else existing_category.dir,
            patterns=new_patterns if new_patterns is not None else existing_category.patterns,
            description=final_description,
        )
    except ValueError as e:
        return ArgValidationError([{"field": "new_name", "message": str(e)}]).to_result().to_json_str()

    def update_category_and_collections(p: Project) -> Project:
        p_without_old = p.without_category(name)
        p_with_new = p_without_old.with_category(updated_category)

        if new_name is not None and new_name != name:
            updated_collections = [
                replace(col, categories=[new_name if c == name else c for c in col.categories])
                for col in p_with_new.collections
            ]
            return replace(p_with_new, collections=updated_collections)

        return p_with_new

    try:
        await session.update_config(update_category_and_collections)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type="save_error").to_json_str()

    change_msg = f"Category '{name}' updated successfully"
    if new_name is not None and new_name != name:
        change_msg = f"Category '{name}' renamed to '{new_name}' successfully"

    return Result.ok(change_msg).to_json_str()
