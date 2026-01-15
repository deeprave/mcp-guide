# See src/mcp_guide/tools/README.md for tool documentation standards

"""Feature flags management tools."""

from typing import Optional

from pydantic import Field

from mcp_core.tool_arguments import ToolArguments
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import validate_flag_name, validate_flag_value
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_NO_PROJECT,
    INSTRUCTION_DISPLAY_ONLY,
    INSTRUCTION_NO_PROJECT,
    INSTRUCTION_VALIDATION_ERROR,
)
from mcp_guide.server import tools

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

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

    feature_name: Optional[str] = Field(None, description="Specific flag name to retrieve")
    active: bool = Field(True, description="Include resolved flags (True) or project-only (False)")


class SetFlagArgs(ToolArguments):
    """Arguments for set_flag tool."""

    feature_name: str = Field(..., description="Flag name to set")
    value: Optional[FeatureValue] = Field(True, description="Flag value to set (True=default, None=remove)")


class GetFlagArgs(ToolArguments):
    """Arguments for get_project_flag tool."""

    feature_name: str = Field(..., description="Flag name to retrieve")


class SetFeatureFlagArgs(ToolArguments):
    """Arguments for set_feature_flag tool."""

    feature_name: str = Field(..., description="Flag name to set")
    value: Optional[FeatureValue] = Field(True, description="Flag value to set (True=default, None=remove)")


class GetFeatureFlagArgs(ToolArguments):
    """Arguments for get_feature_flag tool."""

    feature_name: str = Field(..., description="Flag name to retrieve")


class ListFeatureFlagsArgs(ToolArguments):
    """Arguments for list_feature_flags tool."""

    feature_name: Optional[str] = Field(None, description="Specific flag name to retrieve")
    active: bool = Field(True, description="Include resolved flags (True) or project-only (False)")


async def internal_list_project_flags(
    args: ListFlagsArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[FeatureValue | dict[str, FeatureValue] | None]:
    """List project feature flags based on project context and parameters."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT)

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

        if args.feature_name:
            # Return single flag value
            return Result.ok(flags.get(args.feature_name))
        else:
            # Return all flags
            return Result.ok(flags)

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error")

    except Exception as e:
        return Result.failure(
            f"Failed to list flags: {e}",
            error_type="unexpected_error",
            instruction=INSTRUCTION_DISPLAY_ONLY,
        )


@tools.tool(ListFlagsArgs)
async def list_project_flags(args: ListFlagsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """List project feature flags based on project context and parameters."""
    return (await internal_list_project_flags(args, ctx)).to_json_str()


async def internal_set_project_flag(args: SetFlagArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore[type-arg]
    """Set or remove a project feature flag."""
    # Validate flag arguments
    if not validate_flag_name(args.feature_name):
        return Result.failure(
            f"Invalid flag name '{args.feature_name}'. Flag names must contain only alphanumeric characters, hyphens, and underscores (no periods).",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    if args.value is not None and not validate_flag_value(args.value):
        return Result.failure(
            f"Invalid flag value type. Must be bool, str, list[str], or dict[str, str].",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT)

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
        return Result.failure(f"Failed to save configuration: {e}", error_type="config_write_error")

    except Exception as e:
        return Result.failure(
            f"Failed to set flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        )


@tools.tool(SetFlagArgs)
async def set_project_flag(args: SetFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Set or remove a project feature flag."""
    return (await internal_set_project_flag(args, ctx)).to_json_str()


async def internal_get_project_flag(args: GetFlagArgs, ctx: Optional[Context] = None) -> Result[FeatureValue | None]:  # type: ignore[type-arg]
    """Get a project feature flag value with resolution hierarchy."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT)

    try:
        # Use resolution hierarchy: project → global → None
        from mcp_guide.utils.flag_utils import get_resolved_flag_value

        value = await get_resolved_flag_value(session, args.feature_name)

        return Result.ok(value)

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error")

    except Exception as e:
        return Result.failure(
            f"Failed to get flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        )


@tools.tool(GetFlagArgs)
async def get_project_flag(args: GetFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get a project feature flag value with resolution hierarchy."""
    return (await internal_get_project_flag(args, ctx)).to_json_str()


async def internal_set_feature_flag(args: SetFeatureFlagArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore[type-arg]
    """Set or remove a global feature flag."""
    # Validate flag arguments
    if not validate_flag_name(args.feature_name):
        return Result.failure(
            f"Invalid flag name '{args.feature_name}'. Flag names must contain only alphanumeric characters, hyphens, and underscores (no periods).",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    if args.value is not None and not validate_flag_value(args.value):
        return Result.failure(
            f"Invalid flag value type. Must be bool, str, list[str], or dict[str, str].",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )

    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT)

    # Normalize allow-client-info flag values
    normalized_value = args.value
    if args.feature_name == "allow-client-info" and args.value is not None:
        if args.value in [True, "true", "enabled", "on"]:
            normalized_value = True
        elif args.value in [False, "false", "disabled", "off"]:
            normalized_value = None

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
        return Result.failure(f"Failed to save configuration: {e}", error_type="config_write_error")

    except Exception as e:
        return Result.failure(
            f"Failed to set global flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        )


@tools.tool(SetFeatureFlagArgs)
async def set_feature_flag(args: SetFeatureFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Set or remove a global feature flag."""
    return (await internal_set_feature_flag(args, ctx)).to_json_str()


async def internal_get_feature_flag(
    args: GetFeatureFlagArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[FeatureValue | None]:
    """Get a global feature flag value."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT)

    try:
        # Use global flags only, no resolution hierarchy
        global_proxy = session.feature_flags()
        global_flags = await global_proxy.list()
        value = global_flags.get(args.feature_name)

        return Result.ok(value)

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error")

    except Exception as e:
        return Result.failure(
            f"Failed to get global flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        )


@tools.tool(GetFeatureFlagArgs)
async def get_feature_flag(args: GetFeatureFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get a global feature flag value."""
    return (await internal_get_feature_flag(args, ctx)).to_json_str()


async def internal_list_feature_flags(
    args: ListFeatureFlagsArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[FeatureValue | dict[str, FeatureValue] | None]:
    """List global feature flags."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT)

    try:
        # Global flags only, no merging with project flags
        global_proxy = session.feature_flags()
        flags = await global_proxy.list()

        if args.feature_name:
            # Return single flag value
            return Result.ok(flags.get(args.feature_name))
        else:
            # Return all flags
            return Result.ok(flags)

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error")

    except Exception as e:
        return Result.failure(
            f"Failed to list global flags: {e}",
            error_type="unexpected_error",
            instruction=INSTRUCTION_DISPLAY_ONLY,
        )


@tools.tool(ListFeatureFlagsArgs)
async def list_feature_flags(args: ListFeatureFlagsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """List global feature flags."""
    return (await internal_list_feature_flags(args, ctx)).to_json_str()
