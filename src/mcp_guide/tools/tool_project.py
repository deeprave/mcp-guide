"""Project management tools."""

from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.models import _NAME_REGEX, Category, Collection, Project, format_project_data
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session, list_all_projects
from mcp_guide.session import set_project as session_set_project
from mcp_guide.tools.tool_constants import (
    ERROR_INVALID_NAME,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    ERROR_SAFEGUARD,
    INSTRUCTION_NO_PROJECT,
    INSTRUCTION_NOTFOUND_ERROR,
)

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class GetCurrentProjectArgs(ToolArguments):
    """Arguments for get_project tool."""

    verbose: bool = Field(default=False, description="If True, return full details; if False, return names only")


class SetCurrentProjectArgs(ToolArguments):
    """Arguments for set_project tool."""

    name: str = Field(description="Name of the project to switch to")
    verbose: bool = Field(
        default=False, description="If True, return full project details; if False, return simple confirmation"
    )


class ListProjectsArgs(ToolArguments):
    """Arguments for list_projects tool."""

    verbose: bool = Field(default=False, description="If True, return full details; if False, return names only")


class ListProjectArgs(ToolArguments):
    """Arguments for list_project tool."""

    name: Optional[str] = Field(
        default=None, description="Name of the project to retrieve. If not provided, returns current project."
    )
    verbose: bool = Field(default=False, description="If True, return full details; if False, return basic information")


class CloneProjectArgs(ToolArguments):
    """Arguments for clone_project tool."""

    from_project: str = Field(description="Source project name")
    to_project: Optional[str] = Field(
        default=None, description="Target project name (if None, clones to current project)"
    )
    merge: bool = Field(default=True, description="If True, merge with existing config; if False, replace")
    force: bool = Field(default=False, description="If True, bypass safeguards")


@tools.tool(GetCurrentProjectArgs)
async def get_project(args: GetCurrentProjectArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
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

    result_dict = format_project_data(project, verbose=args.verbose)
    # Include project name in response for single project operations
    result_dict["project"] = project.name

    return Result.ok(result_dict).to_json_str()


@tools.tool(SetCurrentProjectArgs)
async def set_project(args: SetCurrentProjectArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Switch to a different project by name.

    Creates new project with default categories if it doesn't exist. Use verbose=True
    for full project details after switching.

    Args:
        args: Tool arguments with name and verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing switch confirmation and optional project details
    """
    result = await session_set_project(args.name, ctx)

    if result.is_ok():
        project = result.value
        assert project is not None  # is_ok() guarantees value is set

        response = format_project_data(project, verbose=args.verbose)
        # Include project name in response for single project operations
        response["project"] = project.name

        return Result.ok(response, message=f"Switched to project '{project.name}'").to_json_str()

    return result.to_json_str()


@tools.tool(ListProjectsArgs)
async def list_projects(args: ListProjectsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """List all available projects.

    Returns project names (non-verbose) or full project details (verbose).
    Does not require a current project context.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing projects list or dict
    """
    result = await list_all_projects(verbose=args.verbose)
    return result.to_json_str()


@tools.tool(ListProjectArgs)
async def list_project(args: ListProjectArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get information about a specific project by name.

    Returns project details without switching the current project.
    If no name provided, returns current project information.

    Args:
        args: Tool arguments with name and verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing project data
    """
    from mcp_guide.session import get_project_info

    result = await get_project_info(name=args.name, verbose=args.verbose)
    return result.to_json_str()


@tools.tool(CloneProjectArgs)
async def clone_project(args: CloneProjectArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Copy project configuration from one project to another.

    Clones categories and collections from source project to target project.
    Supports merge (combine configs) or replace (overwrite) modes with safeguards.

    Args:
        args: Tool arguments with from_project, to_project, merge, and force flags
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing clone statistics and warnings
    """
    # Validate source project name
    if not args.from_project or not _NAME_REGEX.match(args.from_project):
        return Result.failure(
            f"Invalid source project name '{args.from_project}'",
            error_type=ERROR_INVALID_NAME,
        ).to_json_str()

    # Validate target project name if provided
    if args.to_project is not None and (not args.to_project or not _NAME_REGEX.match(args.to_project)):
        return Result.failure(
            f"Invalid target project name '{args.to_project}'",
            error_type=ERROR_INVALID_NAME,
        ).to_json_str()

    # Get session to access configuration
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        # If we can't get session for current project, we still need to proceed
        # for 2-arg mode where we're not using current project
        if args.to_project is None:
            # 1-arg mode requires current project
            return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()
        # For 2-arg mode, we'll create a temporary session later
        session = None

    # Load all projects atomically through session
    try:
        if session is not None:
            all_projects = await session.get_all_projects()
        else:
            # 2-arg mode without current project - create temporary session
            temp_session = await get_or_create_session(ctx, project_name=args.from_project)
            all_projects = await temp_session.get_all_projects()
            session = temp_session
    except Exception as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    # Check source project exists
    if args.from_project not in all_projects:
        return Result.failure(
            f"Source project '{args.from_project}' not found",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        ).to_json_str()

    source_project = all_projects[args.from_project]

    # Determine target project
    is_current_project = False
    if args.to_project is None:
        # 1-arg mode: clone to current project
        try:
            session = await get_or_create_session(ctx)
            current_project = await session.get_project()
            target_name = current_project.name
            target_project = current_project
            is_current_project = True
        except ValueError as e:
            return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()
    else:
        # 2-arg mode: clone to specified project
        target_name = args.to_project
        target_project_maybe = all_projects.get(target_name)
        if target_project_maybe is None:
            # Create new empty project
            target_project = Project(name=target_name, categories={}, collections={})
        else:
            target_project = target_project_maybe
        # Check if target is current project
        try:
            session = await get_or_create_session(ctx)
            current_project = await session.get_project()
            is_current_project = target_name == current_project.name
        except ValueError:
            pass  # No current project, so target is not current

    # Safeguard: prevent replace mode on non-empty target without force
    if not args.merge and not args.force:
        if target_project.categories or target_project.collections:
            return Result.failure(
                f"Target project '{target_name}' has existing configuration. Use force=True to override or merge=True to merge.",
                error_type=ERROR_SAFEGUARD,
                instruction="Do not retry without explicit user approval for force=True",
            ).to_json_str()

    # Detect conflicts and build warnings
    warnings: list[str] = []
    if args.merge:
        cat_conflicts, coll_conflicts = _detect_conflicts(source_project, target_project)
        if cat_conflicts or coll_conflicts:
            warnings.append(
                f"Merging will overwrite {len(cat_conflicts)} categories and {len(coll_conflicts)} collections"
            )
            for cat_name in cat_conflicts:
                warnings.append(f"Overwritten category '{cat_name}' with different configuration")
            for coll_name in coll_conflicts:
                warnings.append(f"Overwritten collection '{coll_name}' with different configuration")

    # Apply merge or replace logic
    if args.merge:
        merged_cats, cats_added, cats_overwritten = _merge_categories(source_project, target_project)
        merged_colls, colls_added, colls_overwritten = _merge_collections(source_project, target_project)
    else:
        # Replace: copy source entirely
        merged_cats = dict(source_project.categories)
        merged_colls = dict(source_project.collections)
        cats_added = len(merged_cats)
        cats_overwritten = 0
        colls_added = len(merged_colls)
        colls_overwritten = 0

    # Create updated project and save
    updated_project = Project(name=target_name, categories=merged_cats, collections=merged_colls)

    try:
        await session.save_project(updated_project)
    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type="config_write_error").to_json_str()

    # Invalidate cache if current project was modified
    if is_current_project:
        try:
            session = await get_or_create_session(ctx)
            session.invalidate_cache()
        except ValueError:
            pass

    # Build result
    result_dict = {
        "from_project": args.from_project,
        "to_project": target_name,
        "categories_added": cats_added,
        "categories_overwritten": cats_overwritten,
        "collections_added": colls_added,
        "collections_overwritten": colls_overwritten,
        "warnings": warnings,
    }

    return Result.ok(result_dict, message=f"Cloned project '{args.from_project}' to '{target_name}'").to_json_str()


def _detect_conflicts(source: Project, target: Project) -> tuple[list[str], list[str]]:
    """Detect conflicting categories and collections.

    Returns:
        Tuple of (conflicting_category_names, conflicting_collection_names)
    """
    category_conflicts = []
    collection_conflicts = []

    # Build lookup dicts - target is already dict-based
    target_cats = target.categories
    target_colls = target.collections

    # Check categories
    for src_cat_name, src_cat in source.categories.items():
        if src_cat_name in target_cats:
            tgt_cat = target_cats[src_cat_name]
            if (
                src_cat.dir != tgt_cat.dir
                or src_cat.patterns != tgt_cat.patterns
                or src_cat.description != tgt_cat.description
            ):
                category_conflicts.append(src_cat_name)

    # Check collections
    for src_coll_name, src_coll in source.collections.items():
        if src_coll_name in target_colls:
            tgt_coll = target_colls[src_coll_name]
            if src_coll.description != tgt_coll.description or src_coll.categories != tgt_coll.categories:
                collection_conflicts.append(src_coll_name)

    return category_conflicts, collection_conflicts


def _merge_categories(source: Project, target: Project) -> tuple[dict[str, Category], int, int]:
    """Merge categories from source into target.

    Returns:
        Tuple of (merged_categories_dict, added_count, overwritten_count)

    Note:
        This function is intentionally similar to _merge_collections.
        The duplication is minimal and maintains type safety without generic complexity.
    """
    target_cats = dict(target.categories)  # Copy target categories
    added = 0
    overwritten = 0

    for src_cat_name, src_cat in source.categories.items():
        if src_cat_name in target_cats:
            overwritten += 1
        else:
            added += 1
        target_cats[src_cat_name] = src_cat

    return target_cats, added, overwritten


def _merge_collections(source: Project, target: Project) -> tuple[dict[str, Collection], int, int]:
    """Merge collections from source into target.

    Returns:
        Tuple of (merged_collections_dict, added_count, overwritten_count)

    Note:
        This function is intentionally similar to _merge_categories.
        The duplication is minimal and maintains type safety without generic complexity.
    """
    target_colls = dict(target.collections)  # Copy target collections
    added = 0
    overwritten = 0

    for src_coll_name, src_coll in source.collections.items():
        if src_coll_name in target_colls:
            overwritten += 1
        else:
            added += 1
        target_colls[src_coll_name] = src_coll

    return target_colls, added, overwritten
