# See src/mcp_guide/tools/README.md for tool documentation standards

"""Feature flags management tools."""

from fnmatch import fnmatch
from typing import Optional

from fastmcp import Context
from pydantic import Field

from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.feature_flags.constants import FLAG_ALLOW_CLIENT_INFO
from mcp_guide.feature_flags.types import FeatureValue, RawFeatureValue, to_raw_feature_value
from mcp_guide.feature_flags.validators import coerce_boolean_like, validate_flag_name, validate_flag_value
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_CONFIG_READ,
    ERROR_CONFIG_WRITE,
    ERROR_UNEXPECTED,
    ERROR_VALIDATION,
    INSTRUCTION_DISPLAY_ONLY,
    INSTRUCTION_VALIDATION_ERROR,
    make_no_project_result,
)
from mcp_guide.tools.tool_result import tool_result

__all__ = [
    "internal_get_project_flag",
    "internal_set_project_flag",
    "internal_list_project_flags",
    "internal_get_feature_flag",
    "internal_set_feature_flag",
    "internal_list_feature_flags",
]


class ListFlagsArgs(ToolArguments):
    """Arguments for list_flags tool."""

    feature_name: Optional[str] = Field(
        None,
        description="Glob pattern to filter flags (e.g., 'workflow*', 'content-*'). Returns matching flags as dict. Exact match returns single value.",
    )
    active: bool = Field(True, description="Include resolved flags (True) or project-only (False)")


class SetFlagArgs(ToolArguments):
    """Arguments for set_flag tool."""

    feature_name: str = Field(..., description="Flag name to set")
    value: Optional[RawFeatureValue] = Field(True, description="Flag value to set (True=default, None=remove)")


class GetFlagArgs(ToolArguments):
    """Arguments for get_project_flag tool."""

    feature_name: str = Field(..., description="Flag name to retrieve")


class SetFeatureFlagArgs(ToolArguments):
    """Arguments for set_feature_flag tool."""

    feature_name: str = Field(..., description="Flag name to set")
    value: Optional[RawFeatureValue] = Field(True, description="Flag value to set (True=default, None=remove)")


class GetFeatureFlagArgs(ToolArguments):
    """Arguments for get_feature_flag tool."""

    feature_name: str = Field(..., description="Flag name to retrieve")


class ListFeatureFlagsArgs(ToolArguments):
    """Arguments for list_feature_flags tool."""

    feature_name: Optional[str] = Field(
        None,
        description="Glob pattern to filter flags (e.g., 'workflow*', 'content-*'). Returns matching flags as dict. Exact match returns single value.",
    )


def _filter_flags_by_pattern(
    flags: dict[str, FeatureValue],
    pattern: str | None,
) -> RawFeatureValue | dict[str, RawFeatureValue] | None:
    """Filter flags by glob pattern or exact match."""
    if not pattern:
        return {k: to_raw_feature_value(v) for k, v in flags.items()}

    # Check if pattern contains wildcards
    if "*" in pattern or "?" in pattern or "[" in pattern:
        # Glob pattern - return matching flags as dict
        return {k: to_raw_feature_value(v) for k, v in flags.items() if fnmatch(k, pattern)}
    else:
        # Exact match - return single value
        value = flags.get(pattern)
        return to_raw_feature_value(value) if value is not None else None


async def internal_list_project_flags(
    args: ListFlagsArgs,
    ctx: Optional[Context] = None,
) -> Result[RawFeatureValue | dict[str, RawFeatureValue] | None]:
    """List project feature flags based on project context and parameters."""
    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx)
    except ValueError:
        return await make_no_project_result(ctx)

    try:
        if args.active:
            # Merged flags (global + project with project precedence)
            global_proxy = session.feature_flags()
            project_proxy = session.project_flags()
            global_flags = await global_proxy.list()
            project_flags = await project_proxy.list()
            flags = {**global_flags, **project_flags}  # project overrides global
        else:
            # Project flags only
            flags_proxy = session.project_flags()
            flags = await flags_proxy.list()

        return Result.ok(_filter_flags_by_pattern(flags, args.feature_name))

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)

    except Exception as e:
        return Result.failure(
            f"Failed to list flags: {e}",
            error_type=ERROR_UNEXPECTED,
            instruction=INSTRUCTION_DISPLAY_ONLY,
        )


@toolfunc(ListFlagsArgs)
async def list_project_flags(args: ListFlagsArgs, ctx: Optional[Context] = None) -> str:
    """List project feature flags based on project context and parameters.

    Returns flags set for the current project. Use active=True to include resolved values
    from global flags, or active=False for project-only flags. Supports glob pattern filtering.
    """
    result = await internal_list_project_flags(args, ctx)
    return await tool_result("list_project_flags", result)


async def internal_set_project_flag(args: SetFlagArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Set or remove a project feature flag."""
    # Validate flag arguments
    if not validate_flag_name(args.feature_name):
        return Result.failure(
            f"Invalid flag name '{args.feature_name}'. Flag names must contain only alphanumeric characters, hyphens, and underscores (no periods).",
            error_type=ERROR_VALIDATION,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    if args.value is not None and not validate_flag_value(args.value):
        return Result.failure(
            f"Invalid flag value type. Must be bool, str, list[str], or dict[str, str | list[str]].",
            error_type=ERROR_VALIDATION,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx)
    except ValueError:
        return await make_no_project_result(ctx)

    try:
        if args.value is None:
            # Remove flag
            flags_proxy = session.project_flags()
            await flags_proxy.remove(args.feature_name)
            return Result.ok(f"Flag '{args.feature_name}' removed")
        else:
            # Set flag
            flags_proxy = session.project_flags()
            await flags_proxy.set(args.feature_name, args.value)
            return Result.ok(f"Flag '{args.feature_name}' set to {repr(args.value)}")

    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type=ERROR_CONFIG_WRITE)

    except Exception as e:
        return Result.failure(
            f"Failed to set flag: {e}", error_type=ERROR_UNEXPECTED, instruction=INSTRUCTION_DISPLAY_ONLY
        )


@toolfunc(SetFlagArgs)
async def set_project_flag(args: SetFlagArgs, ctx: Optional[Context] = None) -> str:
    """Set or remove a project feature flag.

    Sets a flag value for the current project, or removes it if value=None. Flag names must
    contain only alphanumeric characters, hyphens, and underscores. Values can be bool, str,
    list[str], or dict[str, str].
    """
    result = await internal_set_project_flag(args, ctx)
    return await tool_result("set_project_flag", result)


async def internal_get_project_flag(args: GetFlagArgs, ctx: Optional[Context] = None) -> Result[RawFeatureValue | None]:
    """Get a project feature flag value with resolution hierarchy."""
    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx)
    except ValueError:
        return await make_no_project_result(ctx)

    try:
        # Use resolution hierarchy: project → global → None
        from mcp_guide.feature_flags.utils import get_resolved_flag_value

        value = await get_resolved_flag_value(session, args.feature_name)

        return Result.ok(to_raw_feature_value(value) if value is not None else None)

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)

    except Exception as e:
        return Result.failure(
            f"Failed to get flag: {e}", error_type=ERROR_UNEXPECTED, instruction=INSTRUCTION_DISPLAY_ONLY
        )


async def internal_set_feature_flag(args: SetFeatureFlagArgs, ctx: Optional[Context] = None) -> Result[str]:
    """Set or remove a global feature flag."""
    # Validate flag arguments
    if not validate_flag_name(args.feature_name):
        return Result.failure(
            f"Invalid flag name '{args.feature_name}'. Flag names must contain only alphanumeric characters, hyphens, and underscores (no periods).",
            error_type=ERROR_VALIDATION,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    if args.value is not None and not validate_flag_value(args.value):
        return Result.failure(
            f"Invalid flag value type. Must be bool, str, list[str], or dict[str, str | list[str]].",
            error_type=ERROR_VALIDATION,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx)
    except ValueError:
        return await make_no_project_result(ctx)

    # Normalize allow-client-info through the shared boolean-like coercion rules.
    normalized_value = args.value
    if args.feature_name == FLAG_ALLOW_CLIENT_INFO and args.value is not None:
        coerced = coerce_boolean_like(args.value)
        if coerced is not None:
            normalized_value = coerced

    try:
        if normalized_value is None:
            # Remove flag
            flags_proxy = session.feature_flags()
            await flags_proxy.remove(args.feature_name)
            return Result.ok(f"Global flag '{args.feature_name}' removed")
        else:
            # Set flag
            flags_proxy = session.feature_flags()
            await flags_proxy.set(args.feature_name, normalized_value)
            return Result.ok(f"Global flag '{args.feature_name}' set to {repr(normalized_value)}")

    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type=ERROR_CONFIG_WRITE)

    except Exception as e:
        return Result.failure(
            f"Failed to set global flag: {e}", error_type=ERROR_UNEXPECTED, instruction=INSTRUCTION_DISPLAY_ONLY
        )


@toolfunc(SetFeatureFlagArgs)
async def set_feature_flag(args: SetFeatureFlagArgs, ctx: Optional[Context] = None) -> str:
    """Set or remove a global feature flag.

    Sets a flag value globally (applies to all projects), or removes it if value=None. Flag names
    must contain only alphanumeric characters, hyphens, and underscores. Values can be bool, str,
    list[str], or dict[str, str].
    """
    result = await internal_set_feature_flag(args, ctx)
    return await tool_result("set_feature_flag", result)


async def internal_get_feature_flag(
    args: GetFeatureFlagArgs,
    ctx: Optional[Context] = None,
) -> Result[RawFeatureValue | None]:
    """Get a global feature flag value."""
    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx)
    except ValueError:
        return await make_no_project_result(ctx)

    try:
        # Use global flags only, no resolution hierarchy
        global_proxy = session.feature_flags()
        global_flags = await global_proxy.list()
        value = global_flags.get(args.feature_name)

        return Result.ok(to_raw_feature_value(value) if value is not None else None)

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)

    except Exception as e:
        return Result.failure(
            f"Failed to get global flag: {e}", error_type=ERROR_UNEXPECTED, instruction=INSTRUCTION_DISPLAY_ONLY
        )


async def internal_list_feature_flags(
    args: ListFeatureFlagsArgs,
    ctx: Optional[Context] = None,
) -> Result[RawFeatureValue | dict[str, RawFeatureValue] | None]:
    """List global feature flags."""
    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx)
    except ValueError:
        return await make_no_project_result(ctx)

    try:
        # Global flags only, no merging with project flags
        global_proxy = session.feature_flags()
        flags = await global_proxy.list()

        return Result.ok(_filter_flags_by_pattern(flags, args.feature_name))

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)

    except Exception as e:
        return Result.failure(
            f"Failed to list global flags: {e}",
            error_type=ERROR_UNEXPECTED,
            instruction=INSTRUCTION_DISPLAY_ONLY,
        )


@toolfunc(ListFeatureFlagsArgs)
async def list_feature_flags(args: ListFeatureFlagsArgs, ctx: Optional[Context] = None) -> str:
    """List global feature flags.

    Returns flags set globally (apply to all projects). Supports glob pattern filtering.
    """
    result = await internal_list_feature_flags(args, ctx)
    return await tool_result("list_feature_flags", result)
