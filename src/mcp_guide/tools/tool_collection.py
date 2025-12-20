# See src/mcp_guide/tools/README.md for tool documentation standards

"""Collection management tools."""

from dataclasses import replace
from typing import Any, Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description
from mcp_guide.models import Collection
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_constants import (
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    ERROR_SAVE,
)
from mcp_guide.validation import validate_categories_exist

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

__all__ = [
    "internal_collection_list",
    "internal_collection_add",
    "internal_collection_remove",
    "internal_collection_change",
    "internal_collection_update",
]


class CollectionListArgs(ToolArguments):
    """Arguments for collection_list tool."""

    verbose: bool = Field(default=True, description="If True, return full details; if False, return names only")


async def internal_collection_list(args: CollectionListArgs, ctx: Optional[Context] = None) -> Result[list]:  # type: ignore
    """List all collections in the current project.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing:
        - If verbose=True: list of collection dictionaries with name, categories, description
        - If verbose=False: list of collection names only
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    collections: Any
    if args.verbose:
        collections = [
            {
                "name": name,  # Inject name from dict key
                "categories": list(collection.categories),
                "description": collection.description,
            }
            for name, collection in project.collections.items()  # Use dict.items()
        ]
    else:
        collections = list(project.collections.keys())  # Use dict.keys()

    return Result.ok(collections)


@tools.tool(CollectionListArgs)
async def collection_list(args: CollectionListArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all collections in the current project.

    Retrieves collection information from the current project configuration.
    Useful for discovering available collections before accessing content.

    ## JSON Schema

    ```json
    {
      "type": "object",
      "properties": {
        "verbose": {
          "type": "boolean",
          "description": "If True, return full details; if False, return names only"
        }
      }
    }
    ```

    ## Usage Instructions

    ```python
    # List collection names only
    await collection_list(CollectionListArgs(verbose=False))

    # List full collection details
    await collection_list(CollectionListArgs(verbose=True))
    ```

    ## Concrete Examples

    ```python
    # Example 1: Get collection names for overview
    result = await collection_list(CollectionListArgs(verbose=False))
    # Returns: ["getting-started", "advanced", "reference"]

    # Example 2: Get full collection information
    result = await collection_list(CollectionListArgs(verbose=True))
    # Returns: [{"name": "getting-started", "categories": ["docs", "examples"], "description": "Beginner content"}]
    ```
    """
    result = await internal_collection_list(args, ctx)
    return result.to_json_str()


class CollectionAddArgs(ToolArguments):
    """Arguments for collection_add tool."""

    name: str = Field(..., description="Name of the collection to create")
    description: Optional[str] = Field(None, description="Optional description of the collection's purpose")
    categories: list[str] = Field(
        default_factory=list, description="List of category names to include in the collection"
    )


async def internal_collection_add(args: CollectionAddArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Add a new collection to the current project.

    Args:
        args: Tool arguments with name, description, and categories
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    # Deduplicate while preserving order
    categories = list(dict.fromkeys(args.categories))

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    try:
        # Validate name is not empty
        if not args.name or not args.name.strip():
            raise ArgValidationError([{"field": "name", "message": "Collection name cannot be empty"}])

        # Validate name doesn't contain invalid characters
        if "/" in args.name or "\\" in args.name or " " in args.name or "!" in args.name:
            raise ArgValidationError(
                [{"field": "name", "message": "Collection name cannot contain spaces or special characters"}]
            )

        # Validate name length
        if len(args.name) > 30:
            raise ArgValidationError([{"field": "name", "message": "Collection name must be 30 characters or less"}])

        # Use dict lookup for O(1) duplicate detection
        if args.name in project.collections:
            raise ArgValidationError([{"field": "name", "message": f"Collection '{args.name}' already exists"}])

        validated_description = validate_description(args.description) if args.description else None

        if categories:
            validate_categories_exist(project, categories)
    except ArgValidationError as e:
        return e.to_result()

    try:
        # Create collection without name field (name becomes dict key)
        collection = Collection(categories=categories, description=validated_description)
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result()

    try:
        # Use new dict-based with_collection method
        await session.update_config(lambda p: p.with_collection(args.name, collection))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Collection '{args.name}' added successfully")


@tools.tool(CollectionAddArgs)
async def collection_add(args: CollectionAddArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Add a new collection to the current project.

    Args:
        args: Tool arguments with name, description, and categories
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    result = await internal_collection_add(args, ctx)
    return result.to_json_str()


class CollectionRemoveArgs(ToolArguments):
    """Arguments for collection_remove tool."""

    name: str = Field(..., description="Name of the collection to remove")


async def internal_collection_remove(args: CollectionRemoveArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Remove a collection from the current project.

    Args:
        args: Tool arguments with collection name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.collections:
        return Result.failure(f"Collection '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    try:
        await session.update_config(lambda p: p.without_collection(args.name))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Collection '{args.name}' removed successfully")


@tools.tool(CollectionRemoveArgs)
async def collection_remove(args: CollectionRemoveArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Remove a collection from the current project.

    Args:
        args: Tool arguments with collection name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    result = await internal_collection_remove(args, ctx)
    return result.to_json_str()


class CollectionChangeArgs(ToolArguments):
    """Arguments for collection_change tool."""

    name: str = Field(..., description="Name of the collection to modify")
    new_name: Optional[str] = Field(None, description="New name for the collection")
    new_description: Optional[str] = Field(None, description="New description for the collection")
    new_categories: Optional[list[str]] = Field(None, description="New list of categories to replace existing ones")


async def internal_collection_change(args: CollectionChangeArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Change properties of an existing collection.

    Can change name, description, or categories.
    At least one new value must be provided.
    Changes are saved to the project configuration immediately.

    Args:
        args: Tool arguments with collection name and optional new values
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    existing_collection = project.collections.get(args.name)
    if existing_collection is None:
        return Result.failure(f"Collection '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    if args.new_name is None and args.new_description is None and args.new_categories is None:
        return ArgValidationError(
            [
                {
                    "field": "changes",
                    "message": ("At least one change must be provided (new_name, new_description, or new_categories)"),
                }
            ]
        ).to_result()

    try:
        if args.new_name is not None:
            # Validate new name is not empty
            if not args.new_name or not args.new_name.strip():
                raise ArgValidationError([{"field": "new_name", "message": "Collection name cannot be empty"}])

            # Validate new name doesn't contain invalid characters
            if "/" in args.new_name or "\\" in args.new_name or " " in args.new_name or "!" in args.new_name:
                raise ArgValidationError(
                    [{"field": "new_name", "message": "Collection name cannot contain spaces or special characters"}]
                )

            # Validate new name length
            if len(args.new_name) > 30:
                raise ArgValidationError(
                    [{"field": "new_name", "message": "Collection name must be 30 characters or less"}]
                )

            if args.new_name in project.collections and args.new_name != args.name:
                raise ArgValidationError(
                    [{"field": "new_name", "message": f"Collection '{args.new_name}' already exists"}]
                )

        if args.new_description is not None and args.new_description != "":
            validate_description(args.new_description)

        deduplicated_categories = None
        if args.new_categories is not None:
            deduplicated_categories = list(dict.fromkeys(args.new_categories))
            if deduplicated_categories:
                validate_categories_exist(project, deduplicated_categories)
    except ArgValidationError as e:
        return e.to_result()

    if args.new_description == "":
        final_description = None
    elif args.new_description is not None:
        final_description = args.new_description
    else:
        final_description = existing_collection.description

    final_categories = (
        deduplicated_categories if deduplicated_categories is not None else existing_collection.categories
    )

    try:
        updated_collection = Collection(
            categories=final_categories,
            description=final_description,
        )
    except ValueError as e:
        return ArgValidationError([{"field": "new_name", "message": str(e)}]).to_result()

    try:
        final_name = args.new_name if args.new_name is not None else args.name
        await session.update_config(
            lambda p: p.without_collection(args.name).with_collection(final_name, updated_collection)
        )
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    change_msg = f"Collection '{args.name}' updated successfully"
    if args.new_name is not None and args.new_name != args.name:
        change_msg = f"Collection '{args.name}' renamed to '{args.new_name}' successfully"

    return Result.ok(change_msg)


@tools.tool(CollectionChangeArgs)
async def collection_change(args: CollectionChangeArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Change properties of an existing collection.

    Can change name, description, or categories.
    At least one new value must be provided.
    Changes are saved to the project configuration immediately.

    Args:
        args: Tool arguments with collection name and optional new values
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    result = await internal_collection_change(args, ctx)
    return result.to_json_str()


class CollectionUpdateArgs(ToolArguments):
    """Arguments for collection_update tool."""

    name: str = Field(..., description="Name of the collection to update")
    add_categories: Optional[list[str]] = Field(None, description="Category names to add to the collection")
    remove_categories: Optional[list[str]] = Field(None, description="Category names to remove from the collection")


async def internal_collection_update(args: CollectionUpdateArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Update collection categories incrementally.

    Add or remove categories from a collection without replacing the entire list.
    Categories are removed first, then added (avoiding duplicates).

    Args:
        args: Tool arguments with name and optional add/remove lists
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    existing_collection = project.collections.get(args.name)
    if existing_collection is None:
        return Result.failure(f"Collection '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    if args.add_categories is None and args.remove_categories is None:
        return ArgValidationError(
            [
                {
                    "field": "add_categories",
                    "message": "At least one operation must be provided (add_categories or remove_categories)",
                },
                {
                    "field": "remove_categories",
                    "message": "At least one operation must be provided (add_categories or remove_categories)",
                },
            ]
        ).to_result()

    try:
        if args.add_categories:
            validate_categories_exist(project, args.add_categories)
    except ArgValidationError as e:
        return e.to_result()

    current_categories = list(existing_collection.categories)

    if args.remove_categories:
        current_categories = [c for c in current_categories if c not in args.remove_categories]

    if args.add_categories:
        for category in args.add_categories:
            if category not in current_categories:
                current_categories.append(category)

    # Deduplicate while preserving order
    current_categories = list(dict.fromkeys(current_categories))

    updated_collection = replace(existing_collection, categories=current_categories)

    try:
        await session.update_config(
            lambda p: p.without_collection(args.name).with_collection(args.name, updated_collection)
        )
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Collection '{args.name}' categories updated successfully")


@tools.tool(CollectionUpdateArgs)
async def collection_update(args: CollectionUpdateArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Update collection categories incrementally.

    Add or remove categories from a collection without replacing the entire list.
    Categories are removed first, then added (avoiding duplicates).

    Args:
        args: Tool arguments with name and optional add/remove lists
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    result = await internal_collection_update(args, ctx)
    return result.to_json_str()
