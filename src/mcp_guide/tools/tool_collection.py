"""Collection management tools."""

from dataclasses import replace
from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description
from mcp_guide.models import Collection
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    ERROR_SAVE,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.utils.content_utils import create_file_read_error_result, read_and_render_file_contents, resolve_patterns
from mcp_guide.utils.file_discovery import FileInfo, discover_category_files
from mcp_guide.utils.formatter_selection import get_formatter
from mcp_guide.utils.template_context_cache import get_template_context_if_needed
from mcp_guide.validation import validate_categories_exist

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


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
async def collection_add(args: CollectionAddArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Add a new collection to the current project.

    Args:
        args: Tool arguments with name, description, and categories
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    # Deduplicate while preserving order
    categories = list(dict.fromkeys(args.categories))

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    try:
        if any(col.name == args.name for col in project.collections):
            raise ArgValidationError([{"field": "name", "message": f"Collection '{args.name}' already exists"}])

        validated_description = validate_description(args.description) if args.description else None

        if categories:
            validate_categories_exist(project, categories)
    except ArgValidationError as e:
        return e.to_result().to_json_str()

    try:
        collection = Collection(name=args.name, categories=categories, description=validated_description)
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result().to_json_str()

    try:
        await session.update_config(lambda p: p.with_collection(collection))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Collection '{args.name}' added successfully").to_json_str()


class CollectionRemoveArgs(ToolArguments):
    """Arguments for collection_remove tool."""

    name: str


@tools.tool(CollectionRemoveArgs)
async def collection_remove(args: CollectionRemoveArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Remove a collection from the current project.

    Args:
        args: Tool arguments with collection name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    if all(col.name != args.name for col in project.collections):
        return Result.failure(f"Collection '{args.name}' does not exist", error_type=ERROR_NOT_FOUND).to_json_str()

    try:
        await session.update_config(lambda p: p.without_collection(args.name))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Collection '{args.name}' removed successfully").to_json_str()


class CollectionChangeArgs(ToolArguments):
    """Arguments for collection_change tool."""

    name: str
    new_name: Optional[str] = None
    new_description: Optional[str] = None
    new_categories: Optional[list[str]] = None


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
        JSON string with Result containing success message
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    existing_collection = next((c for c in project.collections if c.name == args.name), None)
    if existing_collection is None:
        return Result.failure(f"Collection '{args.name}' does not exist", error_type=ERROR_NOT_FOUND).to_json_str()

    if args.new_name is None and args.new_description is None and args.new_categories is None:
        return (
            ArgValidationError(
                [
                    {
                        "field": "changes",
                        "message": (
                            "At least one change must be provided (new_name, new_description, or new_categories)"
                        ),
                    }
                ]
            )
            .to_result()
            .to_json_str()
        )

    try:
        if args.new_name is not None and any(
            c.name == args.new_name for c in project.collections if c.name != args.name
        ):
            raise ArgValidationError([{"field": "new_name", "message": f"Collection '{args.new_name}' already exists"}])

        if args.new_description is not None and args.new_description != "":
            validate_description(args.new_description)

        deduplicated_categories = None
        if args.new_categories is not None:
            deduplicated_categories = list(dict.fromkeys(args.new_categories))
            if deduplicated_categories:
                validate_categories_exist(project, deduplicated_categories)
    except ArgValidationError as e:
        return e.to_result().to_json_str()

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
            name=args.new_name if args.new_name is not None else existing_collection.name,
            categories=final_categories,
            description=final_description,
        )
    except ValueError as e:
        return ArgValidationError([{"field": "new_name", "message": str(e)}]).to_result().to_json_str()

    try:
        await session.update_config(lambda p: p.without_collection(args.name).with_collection(updated_collection))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    change_msg = f"Collection '{args.name}' updated successfully"
    if args.new_name is not None and args.new_name != args.name:
        change_msg = f"Collection '{args.name}' renamed to '{args.new_name}' successfully"

    return Result.ok(change_msg).to_json_str()


class CollectionUpdateArgs(ToolArguments):
    """Arguments for collection_update tool."""

    name: str
    add_categories: Optional[list[str]] = None
    remove_categories: Optional[list[str]] = None


@tools.tool(CollectionUpdateArgs)
async def collection_update(args: CollectionUpdateArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Update collection categories incrementally.

    Add or remove categories from a collection without replacing the entire list.
    Categories are removed first, then added (avoiding duplicates).

    Args:
        args: Tool arguments with name and optional add/remove lists
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    existing_collection = next((c for c in project.collections if c.name == args.name), None)
    if existing_collection is None:
        return Result.failure(f"Collection '{args.name}' does not exist", error_type=ERROR_NOT_FOUND).to_json_str()

    if args.add_categories is None and args.remove_categories is None:
        return (
            ArgValidationError(
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
            )
            .to_result()
            .to_json_str()
        )

    try:
        if args.add_categories:
            validate_categories_exist(project, args.add_categories)
    except ArgValidationError as e:
        return e.to_result().to_json_str()

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
        await session.update_config(lambda p: p.without_collection(args.name).with_collection(updated_collection))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Collection '{args.name}' categories updated successfully").to_json_str()


class CollectionContentArgs(ToolArguments):
    """Arguments for collection_content tool."""

    collection: str = Field(description="Name of the collection to retrieve content from")
    pattern: str | None = Field(
        default=None, description="Optional glob pattern to override categories' default patterns"
    )


@tools.tool(CollectionContentArgs)
async def collection_content(
    args: CollectionContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> str:
    """Get aggregated content from all categories in a collection.

    Args:
        args: Tool arguments with collection name and optional pattern
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing formatted content or error
    """
    # Get session
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    # Get project
    project = await session.get_project()

    # Resolve collection
    collection = next((c for c in project.collections if c.name == args.collection), None)
    if collection is None:
        result: Result[str] = Result.failure(
            f"Collection '{args.collection}' not found in project",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
        return result.to_json_str()

    # Validate all categories exist
    for category_name in collection.categories:
        category = next((c for c in project.categories if c.name == category_name), None)
        if category is None:
            result = Result.failure(
                f"Category '{category_name}' (referenced by collection '{args.collection}') not found",
                error_type=ERROR_NOT_FOUND,
                instruction=INSTRUCTION_NOTFOUND_ERROR,
            )
            return result.to_json_str()

    # Aggregate files from all categories
    all_files: list[FileInfo] = []
    file_read_errors: list[str] = []
    docroot = Path(session.get_docroot())

    for category_name in collection.categories:
        category = next(c for c in project.categories if c.name == category_name)

        # Pattern override logic
        patterns = resolve_patterns(args.pattern, category.patterns)

        # Discover files
        category_dir = docroot / category.dir
        files = await discover_category_files(category_dir, patterns)

        # Skip empty categories
        if not files:
            continue

        # Set category and collection fields on all FileInfo objects
        for file in files:
            file.category = category.name
            file.collection = args.collection

        # Read file content with template rendering and modify basename
        template_context = await get_template_context_if_needed(files, category.name)
        errors = await read_and_render_file_contents(
            files, category_dir, template_context, category_prefix=category.name
        )
        file_read_errors.extend(errors)
        all_files.extend(files)

    # Check for file read errors
    if file_read_errors:
        return create_file_read_error_result(
            file_read_errors, args.collection, "collection", ERROR_FILE_READ, INSTRUCTION_FILE_ERROR
        ).to_json_str()

    # Check if any files found
    if not all_files:
        return Result.ok(
            f"No matching content found in collection '{args.collection}'", instruction=INSTRUCTION_PATTERN_ERROR
        ).to_json_str()

    # Format content
    formatter = get_formatter()
    content = await formatter.format(all_files, args.collection)

    return Result.ok(content).to_json_str()
