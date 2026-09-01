# See src/mcp_guide/tools/README.md for tool documentation standards

"""Project management tools."""

from dataclasses import replace
from typing import Any, Literal, Optional

from fastmcp import Context
from pydantic import Field

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.models import Category, Collection, Project, format_project_data
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_CONFIG_READ,
    ERROR_CONFIG_WRITE,
    ERROR_INVALID_NAME,
    ERROR_NOT_FOUND,
    ERROR_PROJECT,
    ERROR_SAFEGUARD,
    ERROR_UNEXPECTED,
    INSTRUCTION_NOTFOUND_ERROR,
    make_invalid_session_result,
    make_no_project_result,
)
from mcp_guide.session import (
    InvalidGuideSessionError,
    get_session,
    list_all_projects,
    mint_modern_session_id,
    retire_minted_session,
)
from mcp_guide.session import set_project as session_set_project
from mcp_guide.tools.tool_helpers import get_session_and_project
from mcp_guide.tools.tool_result import ToolResult, tool_result

logger = get_logger(__name__)

__all__ = [
    "internal_get_project",
    "internal_set_project",
    "internal_switch_project",
    "internal_list_projects",
    "internal_list_project",
    "internal_clone_project",
    "internal_use_project_profile",
    "internal_list_profiles",
    "internal_show_profile",
    "internal_add_permission_path",
    "internal_remove_permission_path",
]


class GetCurrentProjectArgs(ToolArguments):
    """Arguments for get_project tool."""

    verbose: bool = Field(default=False, description="If True, return full details; if False, return names only")


class SetCurrentProjectArgs(ToolArguments):
    """Arguments for set_project tool."""

    path: str = Field(description="Absolute client filesystem path of the project root to bind")
    verbose: bool = Field(
        default=False, description="If True, return full project details; if False, return simple confirmation"
    )


class ListProjectsArgs(ToolArguments):
    """Arguments for list_projects tool."""

    verbose: bool = Field(default=False, description="If True, return full details; if False, return names only")


class SwitchProjectArgs(ToolArguments):
    """Arguments for switching the active configuration within the bound root."""

    name: str = Field(description="Configuration project name to select for the already bound root")
    verbose: bool = Field(
        default=False, description="If True, return full project details; if False, return confirmation"
    )


class ListProjectArgs(ToolArguments):
    """Arguments for list_project tool."""

    name: Optional[str] = Field(
        default=None, description="Name of the project to retrieve. If not provided, returns current project."
    )
    verbose: bool = Field(default=False, description="If True, return full details; if False, return basic information")


class CloneProjectArgs(ToolArguments):
    """Arguments for clone_project tool."""

    from_project: str = Field(
        description="Source project name, or its exact <name>-<hash> configuration key when the name is ambiguous"
    )
    merge: bool = Field(default=True, description="If True, merge with existing config; if False, replace")
    force: bool = Field(default=False, description="If True, bypass safeguards")


async def internal_get_project(args: GetCurrentProjectArgs, ctx: Optional[Context] = None) -> Result[dict]:
    """Get information about the currently active project.

    Returns project name, collections, and categories. Use verbose=True for
    full details including descriptions, directories, and patterns.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing project information
    """
    session, project = await get_session_and_project(ctx, session_id=getattr(args, "session_id", None))
    if project is None:
        return await make_no_project_result()

    result_dict = await format_project_data(project, verbose=args.verbose, session=session)
    # Include project name in response for single project operations
    result_dict["project"] = project.name

    return Result.ok(result_dict)


@toolfunc(GetCurrentProjectArgs)
async def get_project(args: GetCurrentProjectArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Get information about the currently active project.

    Returns project name, collections, and categories. Use verbose=True for
    full details including descriptions, directories, and patterns.
    """
    result = await internal_get_project(args, ctx)
    return await tool_result("get_project", result, ctx=ctx, session_id=args.session_id)


async def internal_set_project(args: SetCurrentProjectArgs, ctx: Optional[Context] = None) -> Result[dict[str, Any]]:
    """Bind this interaction to a client project root.

    Creates new project with default categories if it doesn't exist. Use verbose=True
    for full project details after switching.

    Args:
        args: Tool arguments with absolute path and verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing switch confirmation and optional project details
    """
    session_id = args.session_id
    minted_session_id: str | None = None
    # FastMCP's modern Context exposes the supported persistent session store.
    # Mint only while binding a new modern interaction; retained clients keep
    # their FastMCP connection identity and test callers deliberately avoid an
    # SDK-backed Context.
    if session_id is None and isinstance(ctx, Context):
        request = ctx.request_context
        if request is not None and request.protocol_version == "2026-07-28":
            session_id = await mint_modern_session_id(ctx)
            assert session_id is not None
            minted_session_id = session_id

    set_result: Result[Project] = await session_set_project(args.path, ctx, session_id=session_id)

    if set_result.is_ok():
        project = set_result.value
        assert project is not None  # is_ok() guarantees value is set

        # Get session for flag resolution
        session = None
        try:
            session = await get_session(ctx, session_id=session_id)
        except InvalidGuideSessionError:
            return make_invalid_session_result()
        except ValueError:
            # Continue with session=None, which will include empty flags
            pass

        response = await format_project_data(project, verbose=args.verbose, session=session)

        # Include project name in response for single project operations
        response["project"] = project.name
        if minted_session_id is not None:
            args.session_id = minted_session_id
            response["session_id"] = minted_session_id

        return Result.ok(response, message=f"Bound project root for '{project.name}'")

    # Convert Result[Project] error to Result[dict] error while preserving metadata
    if minted_session_id is not None:
        await retire_minted_session(ctx, minted_session_id)
    return Result.failure(
        set_result.error or "Unknown error",
        error_type=set_result.error_type or ERROR_UNEXPECTED,
        instruction=set_result.instruction,
        message=set_result.message,
    )


@toolfunc(SetCurrentProjectArgs, requires_project=False, binds_project=True)
async def set_project(args: SetCurrentProjectArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Bind this interaction to a client project root.

    Creates new project with default categories if it doesn't exist. Use verbose=True
    for full project details after switching.
    """
    result = await internal_set_project(args, ctx)
    return await tool_result("set_project", result, ctx=ctx, session_id=args.session_id)


async def internal_switch_project(args: SwitchProjectArgs, ctx: Optional[Context] = None) -> Result[dict[str, Any]]:
    """Select a named configuration without changing the bound filesystem root."""
    try:
        session = await get_session(ctx, session_id=args.session_id)
        if not session.project_is_bound:
            return await make_no_project_result()
        await session.switch_project(args.name)
        project = await session.get_project()
        response = await format_project_data(project, verbose=args.verbose, session=session)
        response["project"] = project.name
        return Result.ok(response, message=f"Selected configuration project '{project.name}'")
    except InvalidGuideSessionError:
        return make_invalid_session_result()
    except ValueError as error:
        return Result.failure(str(error), error_type=ERROR_INVALID_NAME)


@toolfunc(SwitchProjectArgs)
async def switch_project(args: SwitchProjectArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Switch active configuration project while retaining the bound root."""
    result = await internal_switch_project(args, ctx)
    return await tool_result("switch_project", result, ctx=ctx, session_id=args.session_id)


async def internal_list_projects(args: ListProjectsArgs, ctx: Optional[Context] = None) -> Result[dict]:
    """List all available projects.

    Returns project names (non-verbose) or full project details (verbose).
    Does not require a current project context.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing projects list or dict
    """
    session = await get_session(ctx, session_id=args.session_id)
    return await list_all_projects(verbose=args.verbose, session=session)


@toolfunc(ListProjectsArgs, requires_project=False)
async def list_projects(args: ListProjectsArgs, ctx: Optional[Context] = None) -> ToolResult:
    """List all available projects.

    Returns project names (non-verbose) or full project details (verbose).
    Does not require a current project context.
    """
    result = await internal_list_projects(args, ctx)
    return await tool_result("list_projects", result, ctx=ctx, session_id=args.session_id)


async def internal_list_project(args: ListProjectArgs, ctx: Optional[Context] = None) -> Result[dict[str, Any]]:
    """Get information about a specific project by name.

    Returns project details without switching the current project.
    If no name provided, returns current project information.

    Args:
        args: Tool arguments with name and verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing project data
    """
    try:
        import dataclasses

        if args.name is None:
            # Get current project - always need session
            session = await get_session(ctx, session_id=args.session_id)
            project = await session.get_project()
            project_name = session.project_name
        else:
            # A configuration key is exact. A display name is accepted only
            # when it selects one strict, valid configuration.
            session = await get_session(ctx, session_id=args.session_id)
            projects = await session.get_all_projects()
            if args.name in projects:
                project = projects[args.name]
            else:
                matches = [(key, candidate) for key, candidate in projects.items() if candidate.name == args.name]
                if not matches:
                    raise ValueError(f"Project '{args.name}' not found")
                if len(matches) > 1:
                    keys = ", ".join(key for key, _candidate in matches)
                    raise ValueError(f"Multiple projects found with name '{args.name}'. Specify one of: {keys}")
                project = matches[0][1]
            project_name = project.name

        # Convert to dict
        data = dataclasses.asdict(project)
        data["project"] = project_name

        # Add flags if verbose and session available
        if args.verbose and session is not None:
            try:
                flags = await session.project_flags().list()
                if flags:
                    data["flags"] = flags
            except Exception:
                pass

        return Result.ok(data)
    except Exception as e:
        return Result.failure(str(e), error_type=ERROR_PROJECT)


@toolfunc(ListProjectArgs)
async def list_project(args: ListProjectArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Get information about a specific project by name.

    Returns project details without switching the current project.
    If no name provided, returns current project information.
    """
    result = await internal_list_project(args, ctx)
    return await tool_result("list_project", result, ctx=ctx, session_id=args.session_id)


async def internal_clone_project(args: CloneProjectArgs, ctx: Optional[Context] = None) -> Result[dict]:
    """Copy project configuration into the currently bound project.

    Clones categories and collections from source project to target project.
    Supports merge (combine configs) or replace (overwrite) modes with safeguards.

    Args:
        args: Tool arguments with from_project, merge, and force flags
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing clone statistics and warnings
    """
    # Validate source project name (allow an exact hash-suffixed key or a
    # valid display name). The target is always the current root-bound project.
    if not args.from_project:
        return Result.failure(
            f"Invalid source project name '{args.from_project}'",
            error_type=ERROR_INVALID_NAME,
        )

    # Check if it's a hash-suffixed key or validate as display name
    from mcp_guide.models import _NAME_REGEX
    from mcp_guide.utils.project_hash import extract_name_from_key

    display_name = extract_name_from_key(args.from_project)
    if not _NAME_REGEX.match(display_name):
        return Result.failure(
            f"Invalid source project name '{args.from_project}'",
            error_type=ERROR_INVALID_NAME,
        )

    # Cloning is only meaningful for an explicitly bound current project.
    try:
        session = await get_session(ctx, session_id=args.session_id)
        current_project = await session.get_project()
    except InvalidGuideSessionError:
        return make_invalid_session_result()
    except ValueError:
        return await make_no_project_result()

    # Resolve the source through the shared configuration.  This admits an
    # exact raw hashless key only as an explicit recovery source; normal
    # project listing and selection remain strict.
    try:
        source_project, ambiguous_keys = await session.resolve_clone_source(args.from_project)
    except Exception as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)

    if ambiguous_keys:
        return Result.failure(
            f"Multiple projects found with name '{args.from_project}'. Please specify the project key: {', '.join(ambiguous_keys)}",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
    if source_project is None:
        return Result.failure(
            f"Source project '{args.from_project}' not found",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )

    target_project = current_project
    target_name = target_project.name

    # Safeguard: prevent replace mode on non-empty target without force
    if not args.merge and not args.force:
        if target_project.categories or target_project.collections:
            return Result.failure(
                f"Target project '{target_name}' has existing configuration. Use force=True to override or merge=True to merge.",
                error_type=ERROR_SAFEGUARD,
                instruction="Do not retry without explicit user approval for force=True",
            )

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
    # Project-level state belongs to the destination identity.  Cloning copies
    # categories and collections into that identity; it must not silently reset
    # flags, permissions, OpenSpec state, or export tracking.
    updated_project = replace(
        target_project,
        categories=merged_cats,
        collections=merged_colls,
    )

    try:
        await session.save_project(updated_project)
    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type=ERROR_CONFIG_WRITE)

    # The Session's own project cache now contains the saved target; reload it
    # through the strict root-bound identity before subsequent tool calls.
    await session.invalidate_cache()

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

    return Result.ok(result_dict, message=f"Cloned project '{args.from_project}' to '{target_name}'")


@toolfunc(CloneProjectArgs)
async def clone_project(args: CloneProjectArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Copy project configuration from one project to another.

    Clones categories and collections from source project to target project.
    Supports merge (combine configs) or replace (overwrite) modes with safeguards.
    """
    result = await internal_clone_project(args, ctx)
    return await tool_result("clone_project", result, ctx=ctx, session_id=args.session_id)


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


class UseProjectProfileArgs(ToolArguments):
    """Arguments for use_project_profile tool."""

    profile: str = Field(description="Name of the profile to apply (e.g., 'python', 'jira')")


async def internal_use_project_profile(args: UseProjectProfileArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Apply a profile to the current project.

    Profiles are additive - they add categories and collections without removing existing ones.
    Applying the same profile multiple times is idempotent (no effect after first application).

    Args:
        args: Profile arguments
        ctx: MCP context

    Returns:
        Result with success message or error
    """
    from mcp_guide.models.profile import Profile

    session, project = await get_session_and_project(ctx, session_id=getattr(args, "session_id", None))
    if project is None:
        return await make_no_project_result()

    # Load profile
    try:
        profile = await Profile.load(args.profile)
    except FileNotFoundError as e:
        return Result.failure(ERROR_NOT_FOUND, message=str(e), instruction=INSTRUCTION_NOTFOUND_ERROR)
    except ValueError as e:
        return Result.failure(ERROR_INVALID_NAME, message=str(e))

    # Apply profile to project (idempotent - won't duplicate existing categories/collections)
    project = profile.apply_to_project(project)

    # Save project
    await session.save_project(project)

    return Result.ok(f"Applied profile '{args.profile}' to project '{project.name}'")


@toolfunc(UseProjectProfileArgs)
async def use_project_profile(args: UseProjectProfileArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Apply a profile to the current project.

    Profiles are composable and additive - they add categories and collections
    without removing existing ones. Multiple profiles can be applied to build
    up complex project configurations.
    """
    result = await internal_use_project_profile(args, ctx)
    return await tool_result("use_project_profile", result, ctx=ctx, session_id=args.session_id)


class ListProfilesArgs(ToolArguments):
    """Arguments for list_profiles tool."""

    category: str | None = Field(
        default=None, description="Optional category name to filter profiles that add or update this category"
    )


async def internal_list_profiles(args: ListProfilesArgs, ctx: Optional[Context] = None) -> Result[list[str]]:
    """List available profiles.

    Args:
        args: List profiles arguments
        ctx: MCP context

    Returns:
        Result with list of profile names
    """
    from mcp_guide.models.profile import Profile, discover_profiles

    all_profiles = await discover_profiles()

    # If no category filter, return all profiles
    if not args.category:
        return Result.ok(all_profiles)

    # Filter profiles by category
    filtered = []
    for profile_name in all_profiles:
        try:
            profile = await Profile.load(profile_name)
            # Check if any category in the profile matches the filter
            if any(cat.name == args.category for cat in profile.categories):
                filtered.append(profile_name)
        except Exception:
            # Skip profiles that fail to load
            continue

    return Result.ok(filtered)


@toolfunc(ListProfilesArgs, requires_project=False)
async def list_profiles(args: ListProfilesArgs, ctx: Optional[Context] = None) -> ToolResult:
    """List available profiles.

    Returns names of pre-configured project profiles. Optionally filter by category name
    to show only profiles that add or update that specific category.
    """
    result = await internal_list_profiles(args, ctx)
    return await tool_result("list_profiles", result, ctx=ctx, session_id=args.session_id)


class ShowProfileArgs(ToolArguments):
    """Arguments for show_profile tool."""

    profile: str = Field(description="Name of the profile to show")


async def internal_show_profile(args: ShowProfileArgs, ctx: Optional[Context] = None) -> Result[dict[str, Any]]:
    """Show profile details.

    Args:
        args: Show profile arguments
        ctx: MCP context

    Returns:
        Result with profile details
    """
    from mcp_guide.models.profile import Profile

    try:
        profile = await Profile.load(args.profile)
    except FileNotFoundError as e:
        return Result.failure(str(e), ERROR_NOT_FOUND, instruction=INSTRUCTION_NOTFOUND_ERROR)
    except ValueError as e:
        return Result.failure(str(e), ERROR_INVALID_NAME)

    # Build categories, omitting null values
    categories = []
    for cat_config in profile.categories:
        cat = {"name": cat_config.name, "patterns": cat_config.patterns}
        if cat_config.dir is not None:
            cat["dir"] = cat_config.dir
        if cat_config.description is not None:
            cat["description"] = cat_config.description
        categories.append(cat)

    # Build collections, omitting null values
    collections = []
    for coll_config in profile.collections:
        coll = {"name": coll_config.name, "categories": coll_config.categories}
        if coll_config.description is not None:
            coll["description"] = coll_config.description
        collections.append(coll)

    # Build result, omitting empty collections
    result_data = {"name": profile.name, "categories": categories}
    if collections:
        result_data["collections"] = collections

    return Result.ok(result_data)


@toolfunc(ShowProfileArgs, requires_project=False)
async def show_profile(args: ShowProfileArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Show profile details.

    Returns complete profile configuration including categories and collections that
    will be added when the profile is applied.
    """
    result = await internal_show_profile(args, ctx)
    return await tool_result("show_profile", result, ctx=ctx, session_id=args.session_id)


# Permission Management Tools


class AddPermissionPathArgs(ToolArguments):
    """Arguments for add_permission_path tool."""

    permission_type: Literal["read", "write"] = Field(description="Permission type: 'read' or 'write'")
    path: str = Field(description="Path to add to permissions")


class RemovePermissionPathArgs(ToolArguments):
    """Arguments for remove_permission_path tool."""

    permission_type: Literal["read", "write"] = Field(description="Permission type: 'read' or 'write'")
    path: str = Field(description="Path to remove from permissions")


async def internal_add_permission_path(args: AddPermissionPathArgs, ctx: Optional[Context] = None) -> Result:
    """Add path to project permissions.

    Args:
        args: Add permission path arguments
        ctx: MCP context

    Returns:
        Result with success message
    """
    from mcp_guide.models.project import Project

    session, project = await get_session_and_project(ctx, session_id=getattr(args, "session_id", None))
    if project is None:
        return await make_no_project_result()

    # Check if already exists (silent success)
    if args.permission_type == "write":
        if args.path in project.allowed_write_paths:
            return Result.ok(f"Path '{args.path}' already in write permissions")

        # Validate using Project model validator
        try:
            Project.validate_allowed_write_paths([args.path])
        except ValueError as e:
            return Result.failure("INVALID_PATH", str(e))

        # Add to write paths
        project.allowed_write_paths.append(args.path)
    else:  # read
        if args.path in project.additional_read_paths:
            return Result.ok(f"Path '{args.path}' already in read permissions")

        # Validate using Project model validator
        try:
            Project.validate_additional_read_paths([args.path])
        except ValueError as e:
            return Result.failure("INVALID_PATH", str(e))

        # Add to read paths
        project.additional_read_paths.append(args.path)

    # Save updated project
    await session.save_project(project)

    return Result.ok(f"Added '{args.path}' to {args.permission_type} permissions")


async def internal_remove_permission_path(args: RemovePermissionPathArgs, ctx: Optional[Context] = None) -> Result:
    """Remove path from project permissions.

    Args:
        args: Remove permission path arguments
        ctx: MCP context

    Returns:
        Result with success message
    """
    session, project = await get_session_and_project(ctx, session_id=getattr(args, "session_id", None))
    if project is None:
        return await make_no_project_result()

    # Remove path based on type (silent success if not found)
    if args.permission_type == "write":
        if args.path in project.allowed_write_paths:
            project.allowed_write_paths.remove(args.path)
            await session.save_project(project)
            return Result.ok(f"Removed '{args.path}' from write permissions")
        return Result.ok(f"Path '{args.path}' not in write permissions")

    else:  # read
        if args.path in project.additional_read_paths:
            project.additional_read_paths.remove(args.path)
            await session.save_project(project)
            return Result.ok(f"Removed '{args.path}' from read permissions")
        return Result.ok(f"Path '{args.path}' not in read permissions")


@toolfunc(AddPermissionPathArgs)
async def add_permission_path(args: AddPermissionPathArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Add path to project permissions.

    Grants read or write permission for the specified path in the current project.
    Paths are stored in project configuration and enforced by the MCP server.
    """
    result = await internal_add_permission_path(args, ctx)
    return await tool_result("add_permission_path", result, ctx=ctx, session_id=args.session_id)


@toolfunc(RemovePermissionPathArgs)
async def remove_permission_path(args: RemovePermissionPathArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Remove path from project permissions.

    Revokes read or write permission for the specified path in the current project.
    The path must have been previously added to permissions.
    """
    result = await internal_remove_permission_path(args, ctx)
    return await tool_result("remove_permission_path", result, ctx=ctx, session_id=args.session_id)
