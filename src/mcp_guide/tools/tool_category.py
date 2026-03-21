# See src/mcp_guide/tools/README.md for tool documentation standards

"""Category management tools."""

import errno
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal, Optional, Union

from anyio import Path as AsyncPath
from pydantic import Field, model_validator

from mcp_guide.content.formatters.selection import ContentFormat, get_formatter_from_flag
from mcp_guide.content.gathering import gather_content
from mcp_guide.content.utils import read_and_render_file_contents
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.core.validation import (
    ArgValidationError,
    validate_description,
    validate_directory_path,
    validate_pattern,
)
from mcp_guide.discovery.files import FileInfo, discover_document_files
from mcp_guide.feature_flags.constants import FLAG_CONTENT_FORMAT
from mcp_guide.feature_flags.utils import get_resolved_flag_value
from mcp_guide.models import Category, CategoryNotFoundError, FileReadError, Project
from mcp_guide.render.cache import get_template_context_if_needed
from mcp_guide.render.frontmatter import get_frontmatter_description_from_file
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    ERROR_SAVE,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.session import get_session
from mcp_guide.tools.tool_result import tool_result

try:
    from fastmcp import Context
except ImportError:
    Context = None  # ty: ignore[invalid-assignment]
logger = get_logger(__name__)

_SERIOUS_ERRNOS = {errno.EACCES, errno.EPERM, errno.EROFS}


def _log_dir_error(log, exc: OSError, category: str, path: object) -> None:
    level = log.warning if exc.errno in _SERIOUS_ERRNOS else log.debug
    level("Failed to create directory for category '%s' at %s: %s", category, path, exc)


__all__ = [
    "internal_category_list",
    "internal_category_add",
    "internal_category_remove",
    "internal_category_change",
    "internal_category_update",
    "internal_category_content",
    "internal_category_list_files",
]


class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool."""

    verbose: bool = Field(default=True, description="If True, return full details; if False, return names only")


class CategoryContentArgs(ToolArguments):
    """Arguments for category_content tool."""

    expression: str = Field(description="Category expression (e.g., 'docs', 'docs/api', 'docs/api+guide')")
    pattern: str | None = Field(
        default=None, description="Optional glob pattern to override category's default patterns"
    )


class CategoryListFilesArgs(ToolArguments):
    """Arguments for category_list_files tool."""

    name: str = Field(description="Name of the category to list files from")


async def internal_category_list(args: CategoryListArgs, ctx: Optional[Context] = None) -> Result[list]:
    """List all categories in the current project.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing:
        - If verbose=True: list of category dictionaries with name, dir, patterns, description
        - If verbose=False: list of category names only
    """
    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    categories: Union[list[dict[str, Union[str, list[str], None]]], list[str]]
    if args.verbose:
        categories = [
            {
                "name": name,  # Inject name from dict key
                "dir": category.dir,
                "patterns": list(category.patterns),  # Convert to list[str]
                "description": category.description,
            }
            for name, category in project.categories.items()  # Use dict.items()
        ]
    else:
        categories = list(project.categories.keys())  # Use dict.keys()

    return Result.ok(categories)


class CategoryAddArgs(ToolArguments):
    """Arguments for category_add tool."""

    name: str = Field(..., description="Name of the category to create")
    dir: Optional[str] = Field(None, description="Directory path relative to docroot (defaults to category name)")
    patterns: list[str] = Field(default_factory=list, description="File patterns to match (e.g., ['*.md', '*.txt'])")
    description: Optional[str] = Field(None, description="Optional description of the category's purpose")


async def internal_category_add(args: CategoryAddArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Add a new category to the current project.

    Args:
        args: Tool arguments with name, dir, patterns, and description
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """

    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    try:
        # Validate name is not empty
        if not args.name or not args.name.strip():
            raise ArgValidationError([{"field": "name", "message": "Category name cannot be empty"}])

        # Validate name doesn't start with underscore (reserved for system categories)
        if args.name.startswith("_"):
            raise ArgValidationError(
                [{"field": "name", "message": "Category names cannot start with underscore (reserved for system use)"}]
            )

        # Validate name doesn't contain invalid characters
        if "/" in args.name or "\\" in args.name or " " in args.name or "!" in args.name:
            raise ArgValidationError(
                [{"field": "name", "message": "Category name cannot contain spaces or special characters"}]
            )

        # Validate name length
        if len(args.name) > 30:
            raise ArgValidationError([{"field": "name", "message": "Category name must be 30 characters or less"}])

        # Use dict lookup for O(1) duplicate detection
        if args.name in project.categories:
            raise ArgValidationError([{"field": "name", "message": f"Category '{args.name}' already exists"}])

        validated_dir = validate_directory_path(args.dir, default=args.name)
        validated_description = validate_description(args.description) if args.description else None

        for pattern in args.patterns:
            validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result()

    try:
        # Create category without name field (name becomes dict key)
        category = Category(dir=validated_dir, patterns=args.patterns, description=validated_description)
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result()

    # Create the directory if it doesn't exist
    try:
        docroot = Path(await session.get_docroot())
        category_dir = docroot / validated_dir
        await AsyncPath(category_dir).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _log_dir_error(logger, exc, args.name, category_dir)
    try:
        # Use new dict-based with_category method
        await session.update_config(lambda p: p.with_category(args.name, category))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Category '{args.name}' added successfully")


class CategoryRemoveArgs(ToolArguments):
    """Arguments for category_remove tool."""

    name: str = Field(..., description="Name of the category to remove")


async def internal_category_remove(args: CategoryRemoveArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Remove a category from the current project.

    Removes the specified category and automatically removes it from all collections.
    Changes are saved to the project configuration immediately.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message

    Examples:
        >>> category_remove(name="docs")
    """

    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.categories:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    def remove_category_and_update_collections(p: Project) -> Project:
        p_without_cat = p.without_category(args.name)
        # Update collections to use dict operations
        updated_collections = {
            name: replace(col, categories=[c for c in col.categories if c != args.name])
            for name, col in p_without_cat.collections.items()
        }
        return replace(p_without_cat, collections=updated_collections)

    try:
        await session.update_config(remove_category_and_update_collections)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Category '{args.name}' removed successfully")


class CategoryChangeArgs(ToolArguments):
    """Arguments for category_change tool."""

    name: str = Field(..., description="Name of the category to modify")
    new_name: Optional[str] = Field(None, description="New name for the category")
    new_dir: Optional[str] = Field(None, description="New directory path for the category")
    new_patterns: Optional[list[str]] = Field(None, description="New file patterns to replace existing ones")
    new_description: Optional[str] = Field(None, description="New description for the category")


async def internal_category_change(args: CategoryChangeArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Change properties of an existing category.

    Args:
        args: Tool arguments with name and optional new values
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """

    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.categories:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    existing_category = project.categories[args.name]

    if args.new_name is None and args.new_dir is None and args.new_patterns is None and args.new_description is None:
        return ArgValidationError(
            [
                {
                    "field": "changes",
                    "message": "At least one change must be provided (new_name, new_dir, new_patterns, or new_description)",
                }
            ]
        ).to_result()

    try:
        if args.new_name is not None:
            # Validate new name is not empty
            if not args.new_name or not args.new_name.strip():
                raise ArgValidationError([{"field": "new_name", "message": "Category name cannot be empty"}])

            # Validate new name doesn't start with underscore (reserved for system categories)
            if args.new_name.startswith("_"):
                raise ArgValidationError(
                    [
                        {
                            "field": "new_name",
                            "message": "Category names cannot start with underscore (reserved for system use)",
                        }
                    ]
                )

            # Validate new name doesn't contain invalid characters
            if "/" in args.new_name or "\\" in args.new_name or " " in args.new_name or "!" in args.new_name:
                raise ArgValidationError(
                    [{"field": "new_name", "message": "Category name cannot contain spaces or special characters"}]
                )

            # Validate new name length
            if len(args.new_name) > 30:
                raise ArgValidationError(
                    [{"field": "new_name", "message": "Category name must be 30 characters or less"}]
                )

            if args.new_name in project.categories and args.new_name != args.name:
                raise ArgValidationError(
                    [{"field": "new_name", "message": f"Category '{args.new_name}' already exists"}]
                )

        if args.new_dir is not None:
            if args.new_dir == "":
                raise ArgValidationError([{"field": "new_dir", "message": "Directory path cannot be empty"}])
            if args.new_dir.startswith("_"):
                raise ArgValidationError([{"field": "new_dir", "message": "Directory cannot start with underscore"}])
            validate_directory_path(args.new_dir, default=args.new_dir)

        if args.new_description is not None and args.new_description != "":
            validate_description(args.new_description)

        if args.new_patterns is not None:
            for pattern in args.new_patterns:
                validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result()

    if args.new_description == "":
        final_description = None
    elif args.new_description is not None:
        final_description = args.new_description
    else:
        final_description = existing_category.description

    try:
        updated_category = Category(
            dir=args.new_dir if args.new_dir is not None else existing_category.dir,
            patterns=args.new_patterns if args.new_patterns is not None else existing_category.patterns,
            description=final_description,
        )
    except ValueError as e:
        return ArgValidationError([{"field": "new_name", "message": str(e)}]).to_result()

    # Create the directory if it's being updated
    if args.new_dir is not None:
        try:
            docroot = Path(await session.get_docroot())
            category_dir = docroot / args.new_dir
            await AsyncPath(category_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _log_dir_error(logger, exc, args.name, category_dir)

    def update_category_and_collections(p: Project) -> Project:
        # Remove old category
        p_without_old = p.without_category(args.name)

        # Add updated category with new or existing name
        final_name = args.new_name if args.new_name is not None else args.name
        p_with_new = p_without_old.with_category(final_name, updated_category)

        # Update collections if category was renamed
        if args.new_name is not None and args.new_name != args.name:
            updated_collections = {
                name: replace(col, categories=[args.new_name if c == args.name else c for c in col.categories])
                for name, col in p_with_new.collections.items()
            }
            return replace(p_with_new, collections=updated_collections)

        return p_with_new

    try:
        await session.update_config(update_category_and_collections)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    change_msg = f"Category '{args.name}' updated successfully"
    if args.new_name is not None and args.new_name != args.name:
        change_msg = f"Category '{args.name}' renamed to '{args.new_name}' successfully"

    return Result.ok(change_msg)


class CategoryUpdateArgs(ToolArguments):
    """Arguments for category_update tool."""

    name: str = Field(..., description="Name of the category to update")
    add_patterns: Optional[list[str]] = Field(None, description="File patterns to add to the category")
    remove_patterns: Optional[list[str]] = Field(None, description="File patterns to remove from the category")


async def internal_category_update(args: CategoryUpdateArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Update category patterns incrementally.

    Args:
        args: Tool arguments with name and pattern changes
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """

    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    existing_category = project.categories.get(args.name)
    if existing_category is None:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    if args.add_patterns is None and args.remove_patterns is None:
        return ArgValidationError(
            [
                {
                    "field": "operations",
                    "message": "At least one operation must be provided (add_patterns or remove_patterns)",
                }
            ]
        ).to_result()

    try:
        if args.add_patterns:
            for pattern in args.add_patterns:
                validate_pattern(pattern)
        if args.remove_patterns:
            for pattern in args.remove_patterns:
                validate_pattern(pattern)
    except ArgValidationError as e:
        return e.to_result()

    current_patterns = list(existing_category.patterns)

    if args.remove_patterns:
        current_patterns = [p for p in current_patterns if p not in args.remove_patterns]

    if args.add_patterns:
        for pattern in args.add_patterns:
            if pattern not in current_patterns:
                current_patterns.append(pattern)

    # Deduplicate while preserving order
    current_patterns = list(dict.fromkeys(current_patterns))

    updated_category = replace(existing_category, patterns=current_patterns)

    def update_category_patterns(p: Project) -> Project:
        return p.without_category(args.name).with_category(args.name, updated_category)

    try:
        await session.update_config(update_category_patterns)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Category '{args.name}' patterns updated successfully")


async def internal_category_list_files(
    args: CategoryListFilesArgs,
    ctx: Optional[Context] = None,
) -> Result[list[dict[str, Any]]]:
    """List all files in a category directory.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing list of file information
    """
    # Get session
    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    # Get project
    project = await session.get_project()

    # Resolve category
    category = project.categories.get(args.name)
    if category is None:
        result: Result[list[dict[str, Any]]] = Result.failure(
            f"Category '{args.name}' not found in project",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
        return result

    # Discover files using **/* pattern to get all files
    docroot = Path(await session.get_docroot())
    category_dir = docroot / category.dir
    files = await discover_document_files(category_dir, ["**/*"])

    # Format as list of file info dictionaries with descriptions
    file_list = []
    for file in files:
        # Extract description from front-matter
        full_path = category_dir / file.path
        description = await get_frontmatter_description_from_file(full_path)

        file_info = {
            "path": file.name,
            "size": file.size,
            "basename": Path(file.name).name,
        }

        # Only add description if it exists
        if description:
            file_info["description"] = description

        file_list.append(file_info)

    return Result.ok(file_list)


@toolfunc(CategoryListFilesArgs)
async def category_list_files(args: CategoryListFilesArgs, ctx: Optional[Context] = None) -> str:
    """List all files in a category directory.

    Returns file information including names, sizes, and modification times for all
    files matching the category's patterns.
    """
    result = await internal_category_list_files(args, ctx)
    return await tool_result("category_list_files", result)


async def internal_category_content(
    args: CategoryContentArgs,
    ctx: Optional[Context] = None,
) -> Result[str]:
    """Get content from a category.

    Args:
        args: Tool arguments with category name and optional pattern
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing formatted content or error
    """
    # Get session
    try:
        session = await get_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    # Get project
    project = await session.get_project()

    try:
        # Build expression with pattern override if provided
        expression = args.expression
        if args.pattern:
            # Apply pattern to all expressions in the input
            if "," in expression:
                # Multiple expressions - apply pattern to each
                parts = [f"{part.strip()}/{args.pattern}" for part in expression.split(",")]
                expression = ",".join(parts)
            else:
                # Single expression
                expression = f"{expression}/{args.pattern}"

        # Delegate to gather_content for file gathering and deduplication
        files = await gather_content(session, project, expression)

        # Check for no matches
        if not files:
            message = (
                f"No files matched pattern '{args.pattern}' in expression '{args.expression}'"
                if args.pattern
                else f"No files found matching expression '{args.expression}'"
            )
            return Result.ok(message, instruction=INSTRUCTION_PATTERN_ERROR)

        # Group files by category for reading (files may span multiple categories)
        docroot = Path(await session.get_docroot())
        files_by_category: dict[str, list[FileInfo]] = {}
        for file in files:
            category_name = (
                file.category.name if file.category else "unknown"
            )  # Category is always set by gather_content
            if category_name not in files_by_category:
                files_by_category[category_name] = []
            files_by_category[category_name].append(file)

        # Read content for each category group
        final_files: list[FileInfo] = []
        file_read_errors: list[str] = []

        for category_name, category_files in files_by_category.items():
            category = project.categories.get(category_name)
            if not category:
                raise CategoryNotFoundError(f"Invalid category '{category_name}' found in FileInfo object")

            category_dir = docroot / category.dir
            template_context = await get_template_context_if_needed(category_files, category_name)

            errors = await read_and_render_file_contents(
                category_files, category_dir, docroot, template_context, category_prefix=category_name
            )
            file_read_errors.extend(errors)
            final_files.extend(category_files)

        # Check for file read errors
        if file_read_errors:
            raise FileReadError(f"Failed to read files: {'; '.join(file_read_errors)}")

        # Resolve content format flag
        flag_value = await get_resolved_flag_value(session, FLAG_CONTENT_FORMAT)
        format_type = ContentFormat.from_flag_value(flag_value)

        # Format and return content
        formatter = get_formatter_from_flag(format_type)
        content = await formatter.format(final_files, docroot)

        return Result.ok(content)

    except CategoryNotFoundError as e:
        return Result.failure(
            str(e),
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
    except FileReadError as e:
        return Result.failure(
            str(e),
            error_type=ERROR_FILE_READ,
            instruction=INSTRUCTION_FILE_ERROR,
        )


@toolfunc(CategoryContentArgs)
async def category_content(
    args: CategoryContentArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Get content from a category.

    Retrieves file content matching the category's directory and patterns. Supports
    optional pattern override for selective content retrieval.
    """
    result = await internal_category_content(args, ctx)
    return await tool_result("category_content", result)


# Consolidated category/collection tools


class CategoryCollectionListArgs(ToolArguments):
    """Arguments for category_collection_list tool."""

    type: Literal["category", "collection"] = Field(description="Type of items to list")
    verbose: bool = Field(default=True, description="If True, return full details; if False, return names only")


async def internal_category_collection_list(
    args: CategoryCollectionListArgs,
    ctx: Optional[Context] = None,
) -> Result[list]:
    """List categories or collections based on type."""
    if args.type == "category":
        category_args = CategoryListArgs(verbose=args.verbose)
        return await internal_category_list(category_args, ctx)
    else:
        from mcp_guide.tools.tool_collection import CollectionListArgs, internal_collection_list

        collection_args = CollectionListArgs(verbose=args.verbose)
        return await internal_collection_list(collection_args, ctx)


@toolfunc(CategoryCollectionListArgs)
async def category_collection_list(
    args: CategoryCollectionListArgs,
    ctx: Optional[Context] = None,
) -> str:
    """List all categories or collections in the current project.

    Returns names only by default, or full details including descriptions, directories,
    and patterns when verbose=True.
    """
    result = await internal_category_collection_list(args, ctx)
    return await tool_result("category_collection_list", result)


class CategoryCollectionRemoveArgs(ToolArguments):
    """Arguments for category_collection_remove tool."""

    type: Literal["category", "collection"] = Field(description="Type of item to remove")
    name: str = Field(description="Name of the item to remove")


async def internal_category_collection_remove(
    args: CategoryCollectionRemoveArgs,
    ctx: Optional[Context] = None,
) -> Result[str]:
    """Remove a category or collection based on type."""
    if args.type == "category":
        category_args = CategoryRemoveArgs(name=args.name)
        return await internal_category_remove(category_args, ctx)
    else:
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, internal_collection_remove

        collection_args = CollectionRemoveArgs(name=args.name)
        return await internal_collection_remove(collection_args, ctx)


@toolfunc(CategoryCollectionRemoveArgs)
async def category_collection_remove(
    args: CategoryCollectionRemoveArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Remove a category or collection from the current project.

    Deletes the specified category or collection by name. This operation cannot be undone.
    Use with caution as removing a category referenced by collections may cause errors.
    """
    result = await internal_category_collection_remove(args, ctx)
    return await tool_result("category_collection_remove", result)


class CategoryCollectionAddArgs(ToolArguments):
    """Arguments for category_collection_add tool."""

    type: Literal["category", "collection"] = Field(description="Type of item to add")
    name: str = Field(description="Name to create")
    description: Optional[str] = Field(None, description="Optional description")
    dir: Optional[str] = Field(None, description="Directory path (category only)")
    patterns: Optional[list[str]] = Field(None, description="File patterns (category only)")
    categories: Optional[list[str]] = Field(None, description="Category expressions (collection only)")

    @model_validator(mode="after")
    def validate_type_fields(self) -> "CategoryCollectionAddArgs":
        """Validate that fields match the specified type."""
        if self.type == "category" and self.categories is not None:
            raise ValueError("'categories' field is only valid for type='collection'")
        if self.type == "collection" and (self.dir is not None or self.patterns is not None):
            raise ValueError("'dir' and 'patterns' fields are only valid for type='category'")
        return self


async def internal_category_collection_add(
    args: CategoryCollectionAddArgs,
    ctx: Optional[Context] = None,
) -> Result[str]:
    """Add a category or collection based on type."""
    if args.type == "category":
        category_args = CategoryAddArgs(
            name=args.name,
            dir=args.dir,
            patterns=args.patterns or [],
            description=args.description,
        )
        return await internal_category_add(category_args, ctx)
    else:
        from mcp_guide.tools.tool_collection import CollectionAddArgs, internal_collection_add

        collection_args = CollectionAddArgs(
            name=args.name,
            description=args.description,
            categories=args.categories or [],
        )
        return await internal_collection_add(collection_args, ctx)


@toolfunc(CategoryCollectionAddArgs)
async def category_collection_add(
    args: CategoryCollectionAddArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Add a new category or collection to the current project.

    Creates a category with directory and file patterns, or a collection grouping
    multiple categories. Category-specific fields (dir, patterns) and collection-specific
    fields (categories) are validated based on the type parameter.
    """
    result = await internal_category_collection_add(args, ctx)
    return await tool_result("category_collection_add", result)


class CategoryCollectionChangeArgs(ToolArguments):
    """Arguments for category_collection_change tool."""

    type: Literal["category", "collection"] = Field(description="Type of item to modify")
    name: str = Field(description="Name to modify")
    new_name: Optional[str] = Field(None, description="New name")
    new_description: Optional[str] = Field(None, description="New description")
    new_dir: Optional[str] = Field(None, description="New directory path (category only)")
    new_patterns: Optional[list[str]] = Field(None, description="New file patterns (category only)")
    new_categories: Optional[list[str]] = Field(None, description="New category list (collection only)")

    @model_validator(mode="after")
    def validate_type_fields(self) -> "CategoryCollectionChangeArgs":
        """Validate that fields match the specified type."""
        if self.type == "category" and self.new_categories is not None:
            raise ValueError("'new_categories' field is only valid for type='collection'")
        if self.type == "collection" and (self.new_dir is not None or self.new_patterns is not None):
            raise ValueError("'new_dir' and 'new_patterns' fields are only valid for type='category'")
        return self


async def internal_category_collection_change(
    args: CategoryCollectionChangeArgs,
    ctx: Optional[Context] = None,
) -> Result[str]:
    """Change a category or collection based on type."""
    if args.type == "category":
        category_args = CategoryChangeArgs(
            name=args.name,
            new_name=args.new_name,
            new_dir=args.new_dir,
            new_patterns=args.new_patterns,
            new_description=args.new_description,
        )
        return await internal_category_change(category_args, ctx)
    else:
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        collection_args = CollectionChangeArgs(
            name=args.name,
            new_name=args.new_name,
            new_description=args.new_description,
            new_categories=args.new_categories,
        )
        return await internal_collection_change(collection_args, ctx)


@toolfunc(CategoryCollectionChangeArgs)
async def category_collection_change(
    args: CategoryCollectionChangeArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Change properties of an existing category or collection.

    Replaces entire property values (name, description, directory, patterns, or categories).
    For incremental updates (adding/removing patterns or categories), use category_collection_update instead.
    """
    result = await internal_category_collection_change(args, ctx)
    return await tool_result("category_collection_change", result)


class CategoryCollectionUpdateArgs(ToolArguments):
    """Arguments for category_collection_update tool."""

    type: Literal["category", "collection"] = Field(description="Type of item to update")
    name: str = Field(description="Name to update")
    add_patterns: Optional[list[str]] = Field(None, description="Patterns to add (category only)")
    remove_patterns: Optional[list[str]] = Field(None, description="Patterns to remove (category only)")
    add_categories: Optional[list[str]] = Field(None, description="Categories to add (collection only)")
    remove_categories: Optional[list[str]] = Field(None, description="Categories to remove (collection only)")

    @model_validator(mode="after")
    def validate_type_fields(self) -> "CategoryCollectionUpdateArgs":
        """Validate that fields match the specified type."""
        if self.type == "category" and (self.add_categories is not None or self.remove_categories is not None):
            raise ValueError("'add_categories' and 'remove_categories' fields are only valid for type='collection'")
        if self.type == "collection" and (self.add_patterns is not None or self.remove_patterns is not None):
            raise ValueError("'add_patterns' and 'remove_patterns' fields are only valid for type='category'")
        return self


async def internal_category_collection_update(
    args: CategoryCollectionUpdateArgs,
    ctx: Optional[Context] = None,
) -> Result[str]:
    """Update a category or collection based on type."""
    if args.type == "category":
        category_args = CategoryUpdateArgs(
            name=args.name,
            add_patterns=args.add_patterns,
            remove_patterns=args.remove_patterns,
        )
        return await internal_category_update(category_args, ctx)
    else:
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        collection_args = CollectionUpdateArgs(
            name=args.name,
            add_categories=args.add_categories,
            remove_categories=args.remove_categories,
        )
        return await internal_collection_update(collection_args, ctx)


@toolfunc(CategoryCollectionUpdateArgs)
async def category_collection_update(
    args: CategoryCollectionUpdateArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Update category or collection incrementally.

    Add or remove individual patterns (for categories) or category references (for collections)
    without replacing the entire list. For complete property replacement, use category_collection_change.
    """
    result = await internal_category_collection_update(args, ctx)
    return await tool_result("category_collection_update", result)
