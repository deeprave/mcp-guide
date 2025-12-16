"""Feature flags management tools."""

from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.feature_flags.resolution import resolve_flag
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value
from mcp_guide.server import tools
from mcp_guide.tools.tool_constants import (
    ERROR_NO_PROJECT,
    INSTRUCTION_DISPLAY_ONLY,
    INSTRUCTION_NO_PROJECT,
    INSTRUCTION_VALIDATION_ERROR,
)

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


def _validate_flag_args(feature_name: str, value: Optional[FeatureValue]) -> Optional[str]:
    """Validate flag arguments. Returns error JSON string if invalid, None if valid."""
    if not validate_flag_name(feature_name):
        return Result.failure(
            f"Invalid flag name '{feature_name}'. Flag names must contain only alphanumeric characters, hyphens, and underscores (no periods).",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        ).to_json_str()

    if value is not None and not validate_flag_value(value):
        return Result.failure(
            f"Invalid flag value type. Must be bool, str, list[str], or dict[str, str].",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        ).to_json_str()
    
    return None


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


@tools.tool(ListFlagsArgs)
async def list_project_flags(args: ListFlagsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """List project feature flags based on project context and parameters."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

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
            return Result.ok(flags.get(args.feature_name)).to_json_str()
        else:
            # Return all flags
            return Result.ok(flags).to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to list flags: {e}",
            error_type="unexpected_error",
            instruction=INSTRUCTION_DISPLAY_ONLY,
        ).to_json_str()


@tools.tool(SetFlagArgs)
async def set_project_flag(args: SetFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Set or remove a project feature flag."""
    # Validate flag arguments
    validation_error = _validate_flag_args(args.feature_name, args.value)
    if validation_error:
        return validation_error

    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        if args.value is None:
            # Remove flag
            flags_proxy = session.project_flags()
            await flags_proxy.remove(args.feature_name)
            return Result.ok(f"Flag '{args.feature_name}' removed").to_json_str()
        else:
            # Set flag
            flags_proxy = session.project_flags()
            await flags_proxy.set(args.feature_name, args.value)
            return Result.ok(f"Flag '{args.feature_name}' set to {repr(args.value)}").to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type="config_write_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to set flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        ).to_json_str()


@tools.tool(GetFlagArgs)
async def get_project_flag(args: GetFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get a project feature flag value with resolution hierarchy."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        # Use resolution hierarchy: project → global → None
        project_proxy = session.project_flags()
        global_proxy = session.feature_flags()
        project_flags = await project_proxy.list()
        global_flags = await global_proxy.list()
        value = resolve_flag(args.feature_name, project_flags, global_flags)

        return Result.ok(value).to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to get flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        ).to_json_str()


@tools.tool(SetFeatureFlagArgs)
async def set_feature_flag(args: SetFeatureFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Set or remove a global feature flag."""
    # Validate flag arguments
    validation_error = _validate_flag_args(args.feature_name, args.value)
    if validation_error:
        return validation_error

    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        if args.value is None:
            # Remove flag
            flags_proxy = session.feature_flags()
            await flags_proxy.remove(args.feature_name)
            return Result.ok(f"Global flag '{args.feature_name}' removed").to_json_str()
        else:
            # Set flag
            flags_proxy = session.feature_flags()
            await flags_proxy.set(args.feature_name, args.value)
            return Result.ok(f"Global flag '{args.feature_name}' set to {repr(args.value)}").to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type="config_write_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to set global flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        ).to_json_str()


@tools.tool(GetFeatureFlagArgs)
async def get_feature_flag(args: GetFeatureFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get a global feature flag value."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        # Use global flags only, no resolution hierarchy
        global_proxy = session.feature_flags()
        global_flags = await global_proxy.list()
        value = global_flags.get(args.feature_name)

        return Result.ok(value).to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to get global flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        ).to_json_str()


@tools.tool(ListFeatureFlagsArgs)
async def list_feature_flags(args: ListFeatureFlagsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """List global feature flags."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        # Global flags only, no merging with project flags
        global_proxy = session.feature_flags()
        flags = await global_proxy.list()

        if args.feature_name:
            # Return single flag value
            return Result.ok(flags.get(args.feature_name)).to_json_str()
        else:
            # Return all flags
            return Result.ok(flags).to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to list global flags: {e}",
            error_type="unexpected_error",
            instruction=INSTRUCTION_DISPLAY_ONLY,
        ).to_json_str()
