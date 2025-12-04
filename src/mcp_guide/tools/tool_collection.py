"""Collection management tools."""

from typing import Any, Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description
from mcp_guide.models import Collection
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.validation import validate_categories_exist

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


# Common error types
ERROR_NO_PROJECT = "no_project"
ERROR_SAVE = "save_error"


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


class CollectionAddArgs(ToolArguments):
    """Arguments for collection_add tool."""

    name: str
    description: Optional[str] = None
    categories: list[str] = Field(default_factory=list)


@tools.tool(CollectionAddArgs)
async def collection_add(
    name: str,
    description: Optional[str] = None,
    categories: Optional[list[str]] = None,
    ctx: Optional[Context] = None,  # type: ignore
) -> str:
    """Add a new collection to the current project.

    Args:
        name: Collection name
        description: Optional description
        categories: Optional list of category names
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    categories = categories or []
    # Deduplicate while preserving order
    categories = list(dict.fromkeys(categories))

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    try:
        if any(col.name == name for col in project.collections):
            raise ArgValidationError([{"field": "name", "message": f"Collection '{name}' already exists"}])

        validated_description = validate_description(description) if description else None

        if categories:
            validate_categories_exist(project, categories)
    except ArgValidationError as e:
        return e.to_result().to_json_str()

    try:
        collection = Collection(name=name, categories=categories, description=validated_description or "")
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result().to_json_str()

    try:
        await session.update_config(lambda p: p.with_collection(collection))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Collection '{name}' added successfully").to_json_str()
